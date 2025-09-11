from db.mysql_connector import get_connection
from utils.security import hash_password  # ✅ PBKDF2 사용
# verify_password는 로그인 검증 시 사용 가능

def insert_user(data):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 이메일 중복 체크
            cursor.execute("SELECT 1 FROM users WHERE email=%s", (data["email"],))
            if cursor.fetchone():
                return {"error": "이미 존재하는 이메일입니다."}, 409

            # PBKDF2 해시 + salt 생성
            pw_hash, salt = hash_password(data["password"])

            cursor.execute("""
                INSERT INTO users (user_id, username, password, salt, email, birth_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data["user_id"],
                data["username"],
                pw_hash,   # 해시
                salt,
                data["email"],
                data["birth_date"]
            ))
        conn.commit()
        return {"message": "회원가입 성공!"}, 201
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500
    finally:
        try: conn.close()
        except: pass


def delete_user(data):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE user_id=%s", (data["user_id"],))
            if cursor.fetchone() is None:
                return {"error": "존재하지 않는 사용자입니다."}, 404

            cursor.execute("DELETE FROM users WHERE user_id=%s", (data["user_id"],))
        conn.commit()
        return {"message": "회원 삭제 성공!"}, 200
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500
    finally:
        try: conn.close()
        except: pass


def get_user_info(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, username, email, phone_number, birth_date, grade, major
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            user = cursor.fetchone()
            if user is None:
                return {"error": "사용자를 찾을 수 없습니다."}, 404
            return {"user": user}, 200
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500
    finally:
        try: conn.close()
        except: pass


def update_password_by_email(email: str, new_password: str):
    """이메일 기준 비밀번호 재설정(PBKDF2)"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
            if cursor.fetchone() is None:
                return {"error": "존재하지 않는 이메일입니다."}, 404

            pw_hash, salt = hash_password(new_password)
            cursor.execute("""
                UPDATE users
                   SET password=%s, salt=%s
                 WHERE email=%s
            """, (pw_hash, salt, email))
        conn.commit()
        return {"message": "비밀번호가 재설정되었습니다."}, 200
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500
    finally:
        try: conn.close()
        except: pass


def get_user_auth(identifier: str):
    """user_id 또는 email 로 사용자 조회"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, email, password, salt
                FROM users
                WHERE user_id=%s OR email=%s
                LIMIT 1
            """, (identifier, identifier))
            return cur.fetchone()
    finally:
        try: conn.close()
        except: pass
