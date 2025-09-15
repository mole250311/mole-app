# db/user/dao.py
from typing import Dict, Any, Optional, Tuple
from db.mysql_connector import get_connection
from utils.security import hash_password  # PBKDF2

# --------------------------------------------------
# 테이블 상수
# --------------------------------------------------
TABLE_USERS = "users"  # (user_id PK/UNIQUE, email UNIQUE 권장)

# --------------------------------------------------
# 회원 가입
# --------------------------------------------------
def insert_user(data: Dict[str, Any]):
    """
    필수: user_id, username, password, email, birth_date
    - email/user_id 중복 409 반환
    - password는 PBKDF2 해시 + salt 저장
    - 반환: dict + status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # user_id 중복 체크
            cur.execute(f"SELECT 1 FROM {TABLE_USERS} WHERE user_id=%s", (data["user_id"],))
            if cur.fetchone():
                return {"error": "이미 존재하는 사용자 ID입니다."}, 409

            # 이메일 중복 체크
            cur.execute(f"SELECT 1 FROM {TABLE_USERS} WHERE email=%s", (data["email"],))
            if cur.fetchone():
                return {"error": "이미 존재하는 이메일입니다."}, 409

            # 해시 생성
            pw_hash, salt = hash_password(data["password"])

            cur.execute(
                f"""
                INSERT INTO {TABLE_USERS}
                  (user_id, username, password, salt, email, birth_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    data["user_id"],
                    data["username"],
                    pw_hash,
                    salt,
                    data["email"],
                    data["birth_date"],
                ),
            )
        conn.commit()
        return {"message": "회원가입 성공!"}, 201
    except Exception as e:
        return {"error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 회원 삭제
# --------------------------------------------------
def delete_user(data: Dict[str, Any]):
    """
    user_id 기준 삭제
    - 존재하지 않으면 404
    - 반환: dict + status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {TABLE_USERS} WHERE user_id=%s", (data["user_id"],))
            if cur.fetchone() is None:
                return {"error": "존재하지 않는 사용자입니다."}, 404

            cur.execute(f"DELETE FROM {TABLE_USERS} WHERE user_id=%s", (data["user_id"],))
        conn.commit()
        return {"message": "회원 삭제 성공!"}, 200
    except Exception as e:
        return {"error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 회원 정보 조회
# --------------------------------------------------
def get_user_info(user_id: str):
    """
    user_id 기준 조회
    - 반환: {"user": row}, 200 | {"error": ...}, 404/500
    - 선택 컬럼: phone_number, grade, major 등 스키마에 맞춰 유지
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT user_id, username, email, phone_number, birth_date, grade, major
                FROM {TABLE_USERS}
                WHERE user_id=%s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if row is None:
                return {"error": "사용자를 찾을 수 없습니다."}, 404
            return {"user": row}, 200
    except Exception as e:
        return {"error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 비밀번호 재설정 (email 기준)
# --------------------------------------------------
def update_password_by_email(email: str, new_password: str):
    """
    email로 사용자 확인 후 PBKDF2로 비밀번호/솔트 갱신
    - 반환: dict + status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {TABLE_USERS} WHERE email=%s", (email,))
            if cur.fetchone() is None:
                return {"error": "존재하지 않는 이메일입니다."}, 404

            pw_hash, salt = hash_password(new_password)
            cur.execute(
                f"""
                UPDATE {TABLE_USERS}
                   SET password=%s, salt=%s
                 WHERE email=%s
                """,
                (pw_hash, salt, email),
            )
        conn.commit()
        return {"message": "비밀번호가 재설정되었습니다."}, 200
    except Exception as e:
        return {"error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 인증용 최소 정보 조회 (로그인/검증용)
# --------------------------------------------------
def get_user_auth(identifier: str):
    """
    user_id 또는 email로 1행 조회
    - 반환: row(dict/tuple) | None (커서 타입에 따름)
    - 로그인 시 verify_password()와 함께 사용
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT user_id, username, email, password, salt
                FROM {TABLE_USERS}
                WHERE user_id=%s OR email=%s
                LIMIT 1
                """,
                (identifier, identifier),
            )
            return cur.fetchone()
    finally:
        try: conn.close()
        except: pass
