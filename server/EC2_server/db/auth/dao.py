from db.mysql_connector import get_connection

def upsert_auth_code(email: str, code: str, ttl_min: int = 10):
    """
    verify_codes 테이블에 인증코드 upsert + 만료시간 설정
    - 만료시간은 DB UTC 시간 기준으로 계산 (UTC_TIMESTAMP() + INTERVAL)
    - 스키마: verify_codes(email PK, code, expires_at)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            q = """
            INSERT INTO verify_codes (email, code, expires_at)
            VALUES (%s, %s, DATE_ADD(UTC_TIMESTAMP(), INTERVAL %s MINUTE))
            ON DUPLICATE KEY UPDATE
              code=VALUES(code),
              expires_at=VALUES(expires_at)
            """
            cur.execute(q, (email, code, ttl_min))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try:
            conn.close()
        except:
            pass


def fetch_auth_code(email: str):
    """
    해당 email의 (code, expires_at) 조회
    - DictCursor/tuple 모두 대응은 호출부에서 처리
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT code, expires_at FROM verify_codes WHERE email=%s",
                (email,)
            )
            return cur.fetchone()  # None 또는 (code, expires_at) / dict
    finally:
        try:
            conn.close()
        except:
            pass


def consume_auth_code(email: str):
    """인증 성공 시 코드 제거(선택)"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM verify_codes WHERE email=%s", (email,))
        conn.commit()
    finally:
        try:
            conn.close()
        except:
            pass

