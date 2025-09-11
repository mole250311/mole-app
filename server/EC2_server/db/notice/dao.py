from db.mysql_connector import get_connection

def get_all_notices():
    """전체 공지사항 조회 (최신순)"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT notice_id, title, content, created_at
                FROM notices
                ORDER BY created_at DESC
            """)
            return cur.fetchall()  # DictCursor면 [{...}, {...}] 반환
    finally:
        try: conn.close()
        except: pass