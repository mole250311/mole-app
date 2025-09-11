from db.mysql_connector import get_connection

def add_favorite(user_id: str, chapter_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
              INSERT INTO user_favorite (user_id, chapter_id)
              VALUES (%s, %s)
            """, (user_id, chapter_id))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        # 중복 방지하려면 UNIQUE(user_id, chapter_id) 인덱스 추가 권장
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

def remove_favorite(user_id: str, chapter_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_favorite WHERE user_id=%s AND chapter_id=%s",
                        (user_id, chapter_id))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

def list_favorites(user_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
              SELECT Favorite_id, user_id, chapter_id
              FROM user_favorite
              WHERE user_id=%s
              ORDER BY Favorite_id DESC
            """, (user_id,))
            return cur.fetchall()
    finally:
        try: conn.close()
        except: pass