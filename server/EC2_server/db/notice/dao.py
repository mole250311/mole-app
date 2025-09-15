# db/notice/dao.py
from typing import List, Dict, Any
from db.mysql_connector import get_connection

# --------------------------------------------------
# 테이블 명 상수 (환경에 맞게 필요 시 수정)
# --------------------------------------------------
TABLE_NOTICE = "notices"  # (notice_id PK, title, content, created_at ...)

# --------------------------------------------------
# 전체 공지사항 조회
# --------------------------------------------------
def get_all_notices(limit: int = 200):
    """
    전체 공지사항을 최신순으로 조회
    - 반환: rows만 반환 (라우트에서 그대로 jsonify)
    - DictCursor면 [{notice_id, title, content, created_at}, ...]
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT notice_id, title, content, created_at
                FROM {TABLE_NOTICE}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (int(limit),),
            )
            return cur.fetchall()
    finally:
        try:
            conn.close()
        except:
            pass

# --------------------------------------------------
# 단일 공지사항 조회
# --------------------------------------------------
def get_notice_by_id(notice_id: int):
    """
    notice_id 기준 단일 공지사항 조회
    - 반환: dict + status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT notice_id, title, content, created_at
                FROM {TABLE_NOTICE}
                WHERE notice_id=%s
                """,
                (int(notice_id),),
            )
            row = cur.fetchone()
            if row:
                return {"notice": row}, 200
            return {"error": "공지사항을 찾을 수 없습니다."}, 404
    except Exception as e:
        return {"error": f"DB 오류: {e}"}, 500
    finally:
        try:
            conn.close()
        except:
            pass
