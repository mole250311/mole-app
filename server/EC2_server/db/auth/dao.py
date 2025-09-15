# db/auth/dao.py
from typing import Optional, Tuple, Dict, Any
from db.mysql_connector import get_connection

# --------------------------------------------------
# 인증코드 저장/갱신 (UPSERT)
# --------------------------------------------------
def upsert_auth_code(email: str, code: str, ttl_min: int = 10):
    """
    verify_codes 테이블에 인증코드 upsert + 만료시간 설정
    - 만료시간은 DB UTC 시간 기준 (UTC_TIMESTAMP() + INTERVAL)
    - 스키마 예시: verify_codes(email PK, code, expires_at)
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
            cur.execute(q, (email, code, int(ttl_min)))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 인증코드 단건 조회
# --------------------------------------------------
def fetch_auth_code(email: str):
    """
    해당 email의 (code, expires_at) 조회
    - 반환: None 또는 튜플/딕셔너리(커서 설정에 따름)
    - 호출부에서 DictCursor/tuple 상황을 처리하도록 유지
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT code, expires_at FROM verify_codes WHERE email=%s",
                (email,)
            )
            return cur.fetchone()
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 인증코드 소비(삭제) - 선택
# --------------------------------------------------
def consume_auth_code(email: str):
    """
    인증 성공 시 코드 제거(선택)
    - 반환: dict + status (원래 형태 유지)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM verify_codes WHERE email=%s", (email,))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 인증코드 검증(만료 포함)
# --------------------------------------------------
def verify_auth_code(email: str, code: str, consume: bool = True):
    """
    - 주어진 (email, code)가 유효한지 검증 (만료시간 포함)
    - 유효하면 consume=True일 때 레코드 삭제
    - 반환: {"ok": True} 또는 {"ok": False, "reason": "..."} 와 status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 코드/만료 동시 확인
            cur.execute(
                """
                SELECT 1
                FROM verify_codes
                WHERE email=%s
                  AND code=%s
                  AND expires_at >= UTC_TIMESTAMP()
                """,
                (email, code),
            )
            row = cur.fetchone()

            if not row:
                # 상세 원인 파악(선택)
                cur.execute(
                    "SELECT code, expires_at FROM verify_codes WHERE email=%s",
                    (email,),
                )
                row2 = cur.fetchone()
                if not row2:
                    return {"ok": False, "reason": "not_found"}, 404
                else:
                    # 코드 불일치 또는 만료
                    return {"ok": False, "reason": "invalid_or_expired"}, 400

            # 유효함 → 필요 시 즉시 소비
            if consume:
                cur.execute("DELETE FROM verify_codes WHERE email=%s", (email,))
            conn.commit()
            return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 만료 레코드 정리 (운영 편의)
# --------------------------------------------------
def purge_expired_codes():
    """
    만료된 인증코드 일괄 삭제
    - 크론/주기적 작업에서 호출하기 좋음
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM verify_codes WHERE expires_at < UTC_TIMESTAMP()")
            deleted = cur.rowcount
        conn.commit()
        return {"ok": True, "deleted": int(deleted)}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass
