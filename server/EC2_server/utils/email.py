# utils/email.py
from __future__ import annotations
import os
import re
import smtplib
import ssl
import time
import uuid
from typing import Optional, Dict, Any
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from email.mime.text import MIMEText

MAIL_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "gmail": {
        "server": os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("GMAIL_SMTP_PORT", "587")),  # 587=STARTTLS, 465=SSL
        "user": os.getenv("GMAIL_USER"),
        "password": os.getenv("GMAIL_PASS"),
        "from_name": os.getenv("GMAIL_FROM_NAME", "EduMolecule"),
    },
    "naver": {
        "server": os.getenv("NAVER_SMTP_SERVER", "smtp.naver.com"),
        "port": int(os.getenv("NAVER_SMTP_PORT", "587")),
        "user": os.getenv("NAVER_USER"),
        "password": os.getenv("NAVER_PASS"),
        "from_name": os.getenv("NAVER_FROM_NAME", "MyApp"),
    },
}

ACTIVE_PROVIDER = os.getenv("MAIL_PROVIDER", "gmail")
DEFAULT_SUBJECT = os.getenv("MAIL_DEFAULT_SUBJECT", "[MyApp] 이메일 인증 코드")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")  # 가벼운 검증용

class MailConfigError(RuntimeError):
    """메일 설정 문제(누락/지원 불가)"""

class MailSendError(RuntimeError):
    """전송 실패(네트워크/SMTP 오류)
    args[0] 예: {"code": 450, "message": "..."}  # code는 없을 수도 있음
    """

def _get_provider(name: Optional[str] = None) -> Dict[str, Any]:
    """환경변수 또는 인자로 선택된 프로바이더 설정 반환."""
    provider_key = (name or ACTIVE_PROVIDER)
    if provider_key not in MAIL_PROVIDERS:
        raise MailConfigError(f"지원하지 않는 PROVIDER: {provider_key}")
    p = MAIL_PROVIDERS[provider_key]
    missing = [k for k in ("server", "port", "user", "password") if not p.get(k)]
    if missing:
        raise MailConfigError(f"메일 설정 누락: {', '.join(missing)} (env 확인)")
    return p

def _validate_email(addr: str) -> None:
    if not addr or not EMAIL_RE.match(addr):
        raise ValueError(f"유효하지 않은 이메일 주소: {addr}")

def _build_message(
    provider_user: str,
    from_name: str,
    to_email: str,
    subject: str,
    body: str,
    reply_to: Optional[str] = None,
) -> MIMEText:
    # 제목 길이 과도 방지(헤더 인코딩 무한 확장 방지)
    subject = (subject or DEFAULT_SUBJECT).strip()
    if len(subject) > 200:
        subject = subject[:197] + "..."

    msg = MIMEText(body or "", _subtype="plain", _charset="utf-8")
    msg["Subject"] = str(Header(subject, "utf-8"))
    msg["From"] = formataddr((str(Header(from_name or "MyApp", "utf-8")), provider_user))
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-Id"] = make_msgid(domain=provider_user.split("@")[-1])
    if reply_to:
        msg["Reply-To"] = reply_to
    return msg

def _send_with_server(
    server_host: str,
    port: int,
    user: str,
    password: str,
    msg: MIMEText,
    timeout: int = 10,
) -> None:
    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(server_host, port, timeout=timeout, context=context) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(server_host, port, timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(user, password)
                server.send_message(msg)
    except smtplib.SMTPResponseException as e:
        # SMTP 코드/메시지 보존
        code = getattr(e, "smtp_code", None)
        err = getattr(e, "smtp_error", b"").decode(errors="ignore")
        raise MailSendError({"code": code, "message": err}) from e
    except (smtplib.SMTPException, OSError) as e:
        raise MailSendError({"message": str(e)}) from e

def send_auth_code_mail(
    to_email: str,
    code: str,
    ttl_min: int = 10,
    subject: Optional[str] = None,
    retries: int = 2,
    backoff_base: float = 0.8,
    provider_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    timeout: int = 10,
) -> None:
    """인증 코드 메일 발송 (실패 시 예외 발생)
    - 라우트 계층에서 이 예외를 잡아 'MAIL_SEND_FAILED' 등으로 매핑하세요.
    - provider_name으로 활성 프로바이더를 오버라이드할 수 있습니다.
    """
    _validate_email(to_email)
    provider = _get_provider(provider_name)

    body = (
        "안녕하세요!\n"
        f"요청하신 인증 코드는 [{code}] 입니다.\n"
        f"{ttl_min}분간 유효합니다."
    ).strip()

    msg = _build_message(
        provider_user=provider["user"],
        from_name=provider.get("from_name", "MyApp"),
        to_email=to_email,
        subject=subject or DEFAULT_SUBJECT,
        body=body,
        reply_to=reply_to,
    )

    last_err: Optional[Exception] = None
    attempts = max(0, int(retries)) + 1
    for i in range(attempts):
        try:
            _send_with_server(
                server_host=provider["server"],
                port=provider["port"],
                user=provider["user"],
                password=provider["password"],
                msg=msg,
                timeout=timeout,
            )
            return  # 성공
        except MailSendError as e:
            last_err = e
        # 지수 백오프 + 지터(0~0.3s)
        if i < attempts - 1:
            sleep_s = (backoff_base ** i) + (uuid.uuid4().int % 300) / 1000.0
            time.sleep(sleep_s)

    # 모든 재시도 실패 → 마지막 오류 전파
    assert last_err is not None
    raise last_err
