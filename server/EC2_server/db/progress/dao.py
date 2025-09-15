# db/progress/dao.py
from typing import Any, Dict, Optional
from db.mysql_connector import get_connection

# --------------------------------------------------
# 테이블 명 상수 (환경에 맞게 필요 시 수정)
# --------------------------------------------------
TABLE_OVERALL = "overall_progress"  # (user_id PK, total_solved INT, total_progress_percent DECIMAL/DOUBLE)

# --------------------------------------------------
# 없으면 0행 생성
# --------------------------------------------------
def ensure_overall_row(user_id: str):
    """
    해당 user_id의 overall_progress가 없으면 (0, 0.0) 으로 생성
    - 반환: 없음 (라우트/호출부에서 필요 시 사용)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {TABLE_OVERALL} (user_id, total_solved, total_progress_percent)
                VALUES (%s, 0, 0.0)
                ON DUPLICATE KEY UPDATE user_id = VALUES(user_id)
                """,
                (user_id,),
            )
        conn.commit()
    finally:
        try:
            conn.close()
        except:
            pass

# --------------------------------------------------
# 전체 진행도 단건 조회
# --------------------------------------------------
def get_overall(user_id: str):
    """
    해당 user_id의 진행도 1행 조회
    - 반환: row(dict/tuple) 1개 또는 None (커서 타입에 따름)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT user_id, total_solved, total_progress_percent
                FROM {TABLE_OVERALL}
                WHERE user_id=%s
                """,
                (user_id,),
            )
            return cur.fetchone()
    finally:
        try:
            conn.close()
        except:
            pass

# --------------------------------------------------
# 진행도 증가 + 퍼센트 재계산
# --------------------------------------------------
def update_overall_increment(user_id: str, solved_delta: int, total_questions: int):
    """
    total_solved를 solved_delta만큼 증가시키고,
    total_progress_percent를 최신 값 기준으로 재계산.
    - total_questions <= 0 이면 퍼센트는 기존 값 유지 (또는 0 처리로 변경 가능)
    - 반환: dict + status
    """
    # 방어적 캐스팅/클램프
    try:
        solved_delta = int(solved_delta)
        total_questions = int(total_questions)
    except Exception:
        return {"ok": False, "error": "invalid parameters"}, 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 없으면 0으로 생성 (user_id가 PK/UNIQUE 여야 함)
            cur.execute(
                f"""
                INSERT INTO {TABLE_OVERALL} (user_id, total_solved, total_progress_percent)
                VALUES (%s, 0, 0.0)
                ON DUPLICATE KEY UPDATE user_id = VALUES(user_id)
                """,
                (user_id,),
            )

            # MySQL은 SET 절이 좌->우 순서로 평가되므로
            # 두 번째 식(total_progress_percent)에서 갱신된 total_solved 사용 가능.
            cur.execute(
                f"""
                UPDATE {TABLE_OVERALL}
                SET total_solved = GREATEST(0, total_solved + %s),
                    total_progress_percent =
                        CASE
                          WHEN %s <= 0 THEN total_progress_percent
                          ELSE LEAST(100.0, ROUND(100.0 * total_solved / %s, 1))
                        END
                WHERE user_id = %s
                """,
                (solved_delta, total_questions, max(total_questions, 1), user_id),
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
# 진행도 값 직접 세팅(동기화용)
# --------------------------------------------------
def set_overall(user_id: str, total_solved: int, total_questions: int):
    """
    total_solved와 percent를 한 번에 세팅.
    - percent = total_questions > 0 ? round(100 * solved / total_questions, 1) : 0.0
    - 0~100 범위로 클램프
    - 반환: dict + status
    """
    try:
        total_solved = max(0, int(total_solved))
        total_questions = int(total_questions)
    except Exception:
        return {"ok": False, "error": "invalid parameters"}, 400

    percent = 0.0
    if total_questions > 0:
        percent = round(100.0 * total_solved / total_questions, 1)
        percent = max(0.0, min(100.0, percent))

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {TABLE_OVERALL} (user_id, total_solved, total_progress_percent)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  total_solved = VALUES(total_solved),
                  total_progress_percent = VALUES(total_progress_percent)
                """,
                (user_id, total_solved, percent),
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
