# db/quiz/dao.py
from typing import List, Dict, Any, Optional, Tuple
from db.mysql_connector import get_connection

# --------------------------------------------------
# 테이블 명 상수 (환경에 맞게 필요 시 수정)
# --------------------------------------------------
TABLE_QUIZ = "quiz"           # 예: quiz (id/quiz_id, amino_acid, question, answer, ...)
TABLE_QUIZ_LOG = "quiz_log"   # (Progress_id, user_id, chapter, quiz_id, status, answered_at)

# --------------------------------------------------
# 퀴즈 목록 - 아미노산(챕터) 기준
# --------------------------------------------------
def get_quizzes_by_amino_acid(amino_acid: str):
    """
    SELECT * FROM quiz WHERE amino_acid = %s ORDER BY id
    원래 형태 유지: dict + status 반환
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 스키마에 id가 없고 quiz_id만 있는 경우 ORDER BY quiz_id로 바꿔도 됨
            sql = "SELECT * FROM quiz WHERE amino_acid = %s ORDER BY id"
            cursor.execute(sql, (amino_acid,))
            quizzes = cursor.fetchall()
            return {"quizzes": quizzes}, 200
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 퀴즈 단건 조회 (id/quiz_id 환경에 맞춰 사용)
# --------------------------------------------------
def get_quiz_by_id(quiz_id: int):
    """
    원래 형태 유지: dict + status 반환
    - 스키마에 따라 id 또는 quiz_id를 사용하세요.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 우선 quiz_id 기준으로 조회, 없으면 id 기준으로 재시도
            try:
                cur.execute(f"SELECT * FROM {TABLE_QUIZ} WHERE quiz_id=%s", (int(quiz_id),))
                row = cur.fetchone()
                if row:
                    return {"quiz": row}, 200
            except Exception:
                pass

            cur.execute(f"SELECT * FROM {TABLE_QUIZ} WHERE id=%s", (int(quiz_id),))
            row = cur.fetchone()
            if row:
                return {"quiz": row}, 200
            return {"error": "퀴즈를 찾을 수 없습니다."}, 404
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 퀴즈 벌크 인서트 (컬럼 키는 실제 스키마에 맞춰 조정)
# --------------------------------------------------
def insert_many_quizzes(rows: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int]:
    """
    rows 예시:
      [{"quiz_id": 1, "amino_acid": "Alanine", "question": "...", "answer": "..."}, ...]
    원래 형태 유지: dict + status 반환
    """
    if not rows:
        return {"ok": True, "inserted": 0}, 200

    cols = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    colnames = ", ".join(cols)
    values = [tuple(row.get(c) for c in cols) for row in rows]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {TABLE_QUIZ} ({colnames}) VALUES ({placeholders})",
                values,
            )
        conn.commit()
        return {"ok": True, "inserted": len(values)}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 전체 퀴즈 개수
# --------------------------------------------------
def get_total_quiz_count() -> int:
    """
    현재 DB에 존재하는 전체 퀴즈 개수 반환
    원래 형태 유지: 숫자만 반환 (라우트에서 그대로 사용)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_QUIZ}")
            (count,) = cur.fetchone()
            return int(count or 0)
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 퀴즈 로그 저장
# --------------------------------------------------
def insert_quiz_log(user_id: str, chapter: str, quiz_id: int, status: str):
    """
    quiz_log(user_id, chapter, quiz_id, status) 에 1행 삽입
    원래 형태 유지: dict + status 반환
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {TABLE_QUIZ_LOG} (user_id, chapter, quiz_id, status)
                VALUES (%s, %s, %s, %s)
            """, (user_id, chapter, quiz_id, status))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

# --------------------------------------------------
# 유저 최근 N개 로그 조회 (디버그/마이페이지용)
# --------------------------------------------------
def get_quiz_logs_by_user(user_id: str, limit: int = 100):
    """
    원래 형태 유지: rows만 반환 (라우트에서 그대로 jsonify)
    스키마에 'question_number'는 없으므로 'quiz_id'를 사용
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
              SELECT Progress_id, user_id, chapter, quiz_id, status, answered_at
              FROM {TABLE_QUIZ_LOG}
              WHERE user_id=%s
              ORDER BY answered_at DESC, Progress_id DESC
              LIMIT %s
            """, (user_id, int(limit)))
            return cur.fetchall()
    finally:
        try: conn.close()
        except: pass
