# db/favorite/dao.py
from typing import List, Dict, Any, Optional, Tuple
from db.mysql_connector import get_connection

# --------------------------------------------------
# 테이블 명 상수 (환경에 맞게 필요 시 수정)
# --------------------------------------------------
TABLE_FAVORITE = "user_favorite"  # (Favorite_id PK, user_id, chapter_id [, created_at ...])

# --------------------------------------------------
# 즐겨찾기 추가
# --------------------------------------------------
def add_favorite(user_id: str, chapter_id: str):
    """
    user_favorite(user_id, chapter_id)에 1행 삽입
    - 중복 방지를 위해 UNIQUE(user_id, chapter_id) 인덱스 권장
    - 반환 형식 유지: dict + status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {TABLE_FAVORITE} (user_id, chapter_id)
                VALUES (%s, %s)
                """,
                (user_id, chapter_id),
            )
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try:
            conn.close()
        except:
            pass

# --------------------------------------------------
# 즐겨찾기 삭제
# --------------------------------------------------
def remove_favorite(user_id: str, chapter_id: str):
    """
    user_favorite에서 해당 (user_id, chapter_id) 레코드 삭제
    - 반환 형식 유지: dict + status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE_FAVORITE} WHERE user_id=%s AND chapter_id=%s",
                (user_id, chapter_id),
            )
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try:
            conn.close()
        except:
            pass

# --------------------------------------------------
# 즐겨찾기 목록 조회
# --------------------------------------------------
def list_favorites(user_id: str, limit: int = 200):
    """
    해당 user_id의 즐겨찾기 목록 조회
    - 반환: rows만 반환 (라우트에서 그대로 jsonify)
    - 스키마에 created_at이 있으면 SELECT 절에 추가 가능
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT Favorite_id, user_id, chapter_id
                FROM {TABLE_FAVORITE}
                WHERE user_id=%s
                ORDER BY Favorite_id DESC
                LIMIT %s
                """,
                (user_id, int(limit)),
            )
            return cur.fetchall()
    finally:
        try:
            conn.close()
        except:
            pass
