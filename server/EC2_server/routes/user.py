# routes/user.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
import os, random
from db.user.dao import (
    insert_user, delete_user, get_user_info,
    update_password_by_email, get_user_auth
)
from db.auth.dao import (
    upsert_auth_code, verify_auth_code
)
from utils.email import send_auth_code_mail
from utils.security import verify_password

user_route = Blueprint("user", __name__)

# -----------------------
# Helper
# -----------------------
def _json():
    return request.get_json(silent=True) or {}

def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code

def _err(msg: str, code: int, *, error_code: str = None, details: dict | None = None):
    body = {"ok": False, "error": msg}
    if error_code: body["code"] = error_code
    if details: body["details"] = details
    return jsonify(body), code


# -----------------------
# 회원가입
# -----------------------
@user_route.route("/users/register", methods=["POST"])
def register_user():
    data = _json()
    required = ["user_id", "username", "password", "email", "birth_date"]
    if not all(k in data and str(data[k]).strip() for k in required):
        return _err("모든 필드를 입력해주세요.", 400, error_code="MISSING_FIELDS")

    result, status = insert_user(data)
    if status == 409:
        return _err(result.get("error","중복된 계정"), 409, error_code="DUPLICATE_USER")
    if status != 201:
        return _err(result.get("error","DB 오류"), 500, error_code="DB_ERROR")
    return _ok({"ok": True, "message": "회원가입 성공!"}, 201)


# -----------------------
# 회원 삭제
# -----------------------
@user_route.route("/users/delete", methods=["POST"])
def delete_user_route():
    data = _json()
    user_id = str(data.get("user_id","")).strip()
    if not user_id:
        return _err("user_id는 필수입니다.", 400, error_code="MISSING_USER_ID")

    result, status = delete_user({"user_id": user_id})
    if status == 404:
        return _err("존재하지 않는 사용자입니다.", 404, error_code="NOT_FOUND")
    if status != 200:
        return _err("삭제 처리 실패", 500, error_code="DB_ERROR")
    return _ok({"ok": True, "message": "회원 삭제 성공!"})


# -----------------------
# 회원 정보 조회
# -----------------------
@user_route.route("/users/info", methods=["GET"])
def get_user_info_route():
    user_id = str(request.args.get("user_id","")).strip()
    if not user_id:
        return _err("user_id가 필요합니다.", 400, error_code="MISSING_USER_ID")

    result, status = get_user_info(user_id)
    if status == 404:
        return _err("사용자를 찾을 수 없습니다.", 404, error_code="NOT_FOUND")
    if status != 200:
        return _err("조회 실패", 500, error_code="DB_ERROR")
    return _ok({"ok": True, "user": result["user"]})


# -----------------------
# 이메일 인증코드 발송
# -----------------------
@user_route.route("/users/send-code", methods=["POST"])
def send_auth_code_route():
    data = _json()
    email = str(data.get("email","")).strip()
    if not email:
        return _err("email이 필요합니다.", 400, error_code="MISSING_EMAIL")

    # 개발 모드 고정 코드
    auth_code = os.getenv("AUTH_CODE_FIXED") or f"{random.randint(0,999999):06d}"

    result, status = upsert_auth_code(email, auth_code, ttl_min=10)
    if status != 200:
        return _err(result.get("error","DB 오류"), 500, error_code="DB_ERROR")

    try:
        send_auth_code_mail(email, auth_code)
    except Exception as e:
        return _err("이메일 발송 실패", 502, error_code="MAIL_SEND_FAILED", details={"reason": str(e)})

    return _ok({"ok": True, "message": "인증 코드 발송 완료"})


# -----------------------
# 이메일 인증코드 검증
# -----------------------
@user_route.route("/users/verify-code", methods=["POST"])
def verify_auth_code_route():
    data = _json()
    email = str(data.get("email","")).strip()
    code  = str(data.get("code","")).strip()
    if not email or not code:
        return _err("email, code 모두 필요", 400, error_code="MISSING_FIELDS")

    result, status = verify_auth_code(email, code, consume=True)
    if status == 404:
        return _err("코드가 존재하지 않음", 404, error_code="CODE_NOT_FOUND")
    if status == 400:
        return _err("코드 불일치 또는 만료", 400, error_code="INVALID_CODE")
    if status != 200:
        return _err("DB 오류", 500, error_code="DB_ERROR")

    return _ok({"ok": True, "message": "인증 성공"})


# -----------------------
# 비밀번호 재설정
# -----------------------
@user_route.route("/users/reset-password", methods=["POST"])
def reset_password_route():
    data = _json()
    email = str(data.get("email","")).strip()
    new_pw = str(data.get("new_password",""))

    if not email or not new_pw:
        return _err("email, new_password 모두 필요", 400, error_code="MISSING_FIELDS")
    if len(new_pw) < 8:
        return _err("비밀번호는 8자 이상이어야 합니다.", 400, error_code="PASSWORD_TOO_SHORT")

    result, status = update_password_by_email(email, new_pw)
    if status == 404:
        return _err("존재하지 않는 이메일입니다.", 404, error_code="NOT_FOUND")
    if status != 200:
        return _err("DB 오류", 500, error_code="DB_ERROR")

    return _ok({"ok": True, "message": "비밀번호 재설정 성공"})


# -----------------------
# 로그인
# -----------------------
@user_route.route("/users/login", methods=["POST"])
def login_user_route():
    data = _json()
    identifier = str(data.get("identifier","")).strip()
    password   = str(data.get("password",""))

    if not identifier or not password:
        return _err("identifier, password 모두 필요", 400, error_code="MISSING_FIELDS")

    row = get_user_auth(identifier)
    if not row:
        return _err("아이디/이메일 또는 비밀번호가 올바르지 않습니다.", 401, error_code="INVALID_CREDENTIALS")

    if isinstance(row, dict):
        user_id, username, email, pw_hash, salt = (
            row["user_id"], row["username"], row["email"], row["password"], row["salt"]
        )
    else:
        user_id, username, email, pw_hash, salt = row

    if not verify_password(password, pw_hash, salt):
        return _err("아이디/이메일 또는 비밀번호가 올바르지 않습니다.", 401, error_code="INVALID_CREDENTIALS")

    return _ok({
        "ok": True,
        "user": {"user_id": user_id, "username": username, "email": email}
    })
