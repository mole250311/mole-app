from db.mysql_connector import get_connection

def ensure_overall_row(user_id: str):
    """없으면 0으로 생성"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
              INSERT INTO overall_progress (user_id, total_solved, total_progress_percent)
              VALUES (%s, 0, 0.0)
              ON DUPLICATE KEY UPDATE user_id=user_id
            """, (user_id,))
        conn.commit()
    finally:
        try: conn.close()
        except: pass

def get_overall(user_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
              SELECT user_id, total_solved, total_progress_percent
              FROM overall_progress WHERE user_id=%s
            """, (user_id,))
            return cur.fetchone()
    finally:
        try: conn.close()
        except: pass

def update_overall_increment(user_id: str, solved_delta: int, total_questions: int):
    """
    문제 풀이 1건 처리 후 누적 업데이트.
    solved_delta: 정답이면 1, 오답이면 0 (원하면 시도만 해도 +1로 바꿔도 됨)
    total_questions: 전체 문항 수(퍼센트 계산용)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 없을 수 있으니 먼저 보장
            cur.execute("""
              INSERT INTO overall_progress (user_id, total_solved, total_progress_percent)
              VALUES (%s, 0, 0.0)
              ON DUPLICATE KEY UPDATE user_id=user_id
            """, (user_id,))
            # 누적 solved 업데이트
            cur.execute("""
              UPDATE overall_progress
              SET total_solved = total_solved + %s,
                  total_progress_percent =
                    CASE
                      WHEN %s <= 0 THEN total_progress_percent
                      ELSE ROUND(100.0 * (total_solved + %s) / %s, 1)
                    END
              WHERE user_id=%s
            """, (solved_delta, total_questions, solved_delta, total_questions, user_id))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

def set_overall(user_id: str, total_solved: int, total_questions: int):
    """한 번에 값 세팅(동기화용)"""
    percent = round(100.0 * total_solved / total_questions, 1) if total_questions > 0 else 0.0
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
              INSERT INTO overall_progress (user_id, total_solved, total_progress_percent)
              VALUES (%s, %s, %s)
              ON DUPLICATE KEY UPDATE
                total_solved=VALUES(total_solved),
                total_progress_percent=VALUES(total_progress_percent)
            """, (user_id, total_solved, percent))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass