from flask import Blueprint, request, jsonify
from db.user.dao import insert_user, delete_user, get_user_info, update_password_by_email, get_user_auth
from db.auth.dao import upsert_auth_code, fetch_auth_code, consume_auth_code  # ✅ 인증코드 DB upsert는 auth/dao.py로
from utils.email import send_auth_code_mail
from utils.security import verify_password
import random
import datetime

user_route = Blueprint("user", __name__)

@user_route.route("/users/register", methods=["POST"])
def register_user():
    data = request.get_json()
    required_fields = ["user_id", "username", "password", "email", "birth_date"]

    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"error": "모든 필드를 입력해주세요."}), 400

    result, status = insert_user(data)
    return jsonify(result), status


@user_route.route("/users/delete", methods=["POST"])
def delete_user_route():
    data = request.get_json()
    if not data.get("user_id"):
        return jsonify({"error": "user_id는 필수입니다."}), 400

    result, status = delete_user(data)
    return jsonify(result), status


@user_route.route("/users/info", methods=["GET"])
def get_user_info_route():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id가 필요합니다."}), 400

    result, status = get_user_info(user_id)
    return jsonify(result), status


# -----------------------------
# 이메일 인증코드 발송 (/users/send-code)
# -----------------------------
@user_route.route("/users/send-code", methods=["POST"])
def send_auth_code_route():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "email이 필요합니다."}), 400

    # 1) 코드 생성 (개발 중이면 고정코드 써도 됨: auth_code = "0000")
    auth_code = f"{random.randint(0, 999999):06d}"

    # 2) DB 저장 (auth_codes upsert) – auth/dao.py 사용
    result, status = upsert_auth_code(email, auth_code, ttl_min=10)
    if status != 200:
        return jsonify(result), status

    try:
        send_auth_code_mail(email, auth_code)
    except Exception as e:
        return jsonify({"error": f"이메일 발송 실패: {e}"}), 500

    return jsonify({"message": "인증 코드 발송 완료"}), 200

@user_route.route("/users/verify-code", methods=["POST"])
def verify_auth_code_route():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    code  = data.get("code")
    if not email or not code:
        return jsonify({"ok": False, "error": "email, code 모두 필요"}), 400

    row = fetch_auth_code(email)
    if not row:
        return jsonify({"ok": False, "error": "코드가 존재하지 않음"}), 404

    # DictCursor / tuple 모두 대응
    if isinstance(row, dict):
        saved_code, expires_at = row["code"], row["expires_at"]
    else:
        saved_code, expires_at = row[0], row[1]

    # 만료 체크 (UTC 기준)
    now = datetime.datetime.utcnow()
    if isinstance(expires_at, str):
        # MySQL DATETIME을 문자열로 받는 경우
        try:
            # 'YYYY-MM-DD HH:MM:SS' 형태 처리
            expires_at = datetime.datetime.fromisoformat(expires_at)
        except ValueError:
            # 수동 파싱
            expires_at = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")

    if now > expires_at:
        return jsonify({"ok": False, "error": "코드 만료"}), 400

    if str(saved_code) != str(code):
        return jsonify({"ok": False, "error": "코드 불일치"}), 400

    # 성공 시 1회용으로 제거(선택)
    consume_auth_code(email)
    return jsonify({"ok": True, "message": "인증 성공"}), 200

@user_route.route("/users/reset-password", methods=["POST"])
def reset_password_route():
    """
    Body JSON:
    {
      "email": "user@example.com",
      "new_password": "NewP@ssw0rd!"
    }
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    new_password = data.get("new_password")

    if not email or not new_password:
        return jsonify({"ok": False, "error": "email, new_password 모두 필요"}), 400

    # (선택) 비밀번호 정책
    if len(new_password) < 8:
        return jsonify({"ok": False, "error": "비밀번호는 8자 이상이어야 합니다."}), 400

    # DB 업데이트 (※ update_password_by_email이 내부에서 해싱한다는 가정)
    result, status = update_password_by_email(email, new_password)
    if status != 200:
        return jsonify({"ok": False, **result}), status

    return jsonify({"ok": True, "message": "비밀번호가 재설정되었습니다."}), 200

@user_route.route("/users/login", methods=["POST"])
def login_user_route():
    """
    Body:
    { "identifier": "user_id 또는 email", "password": "평문비번" }
    """
    data = request.get_json(silent=True) or {}
    identifier = data.get("identifier")
    password = data.get("password")

    if not identifier or not password:
        return jsonify({"ok": False, "error": "identifier, password 모두 필요"}), 400

    row = get_user_auth(identifier)
    if not row:
        return jsonify({"ok": False, "error": "아이디/이메일 또는 비밀번호가 올바르지 않습니다."}), 401

    # DictCursor or tuple
    if isinstance(row, dict):
        user_id, username, email, pw_hash, salt = row["user_id"], row["username"], row["email"], row["password"], row["salt"]
    else:
        user_id, username, email, pw_hash, salt = row

    if not verify_password(password, pw_hash, salt):
        return jsonify({"ok": False, "error": "아이디/이메일 또는 비밀번호가 올바르지 않습니다."}), 401

    return jsonify({
        "ok": True,
        "user": {
            "user_id": user_id,
            "username": username,
            "email": email
        }
    }), 200