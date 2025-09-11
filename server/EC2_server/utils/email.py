import os
import smtplib
import ssl
import time
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText

MAIL_PROVIDERS = {
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

class MailConfigError(RuntimeError):
    pass

def _get_provider():
    if ACTIVE_PROVIDER not in MAIL_PROVIDERS:
        raise MailConfigError(f"지원하지 않는 PROVIDER: {ACTIVE_PROVIDER}")
    p = MAIL_PROVIDERS[ACTIVE_PROVIDER]
    missing = [k for k in ("server", "port", "user", "password") if not p.get(k)]
    if missing:
        raise MailConfigError(f"메일 설정 누락: {', '.join(missing)} (env 확인)")
    return p

def _build_message(provider_user: str, from_name: str, to_email: str, subject: str, body: str) -> MIMEText:
    # 한글 본문/제목 인코딩 안전
    msg = MIMEText(body, _subtype="plain", _charset="utf-8")
    msg["Subject"] = str(Header(subject, "utf-8"))
    # 표시명(한글 가능) + 실제 주소
    msg["From"] = formataddr((str(Header(from_name, "utf-8")), provider_user))
    msg["To"] = to_email
    return msg

def _send_with_server(server_host: str, port: int, user: str, password: str, msg: MIMEText, timeout: int = 10):
    # 465면 SSL 직결, 587이면 STARTTLS
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

def send_auth_code_mail(to_email: str, code: str, ttl_min: int = 10, subject: str | None = None, retries: int = 2, backoff_sec: float = 1.5) -> None:
    """
    인증 코드 메일 발송 (실패 시 예외 발생)
    - 예외가 올라오면 라우트에서 DB에 저장한 인증코드 롤백/소비 처리 권장
    """
    provider = _get_provider()

    body = (
        "안녕하세요!\n"
        f"요청하신 인증 코드는 [{code}] 입니다.\n"
        f"{ttl_min}분간 유효합니다."
    )
    msg = _build_message(
        provider_user=provider["user"],
        from_name=provider.get("from_name", "MyApp"),
        to_email=to_email,
        subject=subject or DEFAULT_SUBJECT,
        body=body,
    )

    last_err = None
    for attempt in range(retries + 1):
        try:
            _send_with_server(
                server_host=provider["server"],
                port=provider["port"],
                user=provider["user"],
                password=provider["password"],
                msg=msg,
            )
            return  # 성공
        except (smtplib.SMTPException, OSError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff_sec * (attempt + 1))
            else:
                raise