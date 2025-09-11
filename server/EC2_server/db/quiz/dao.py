from db.mysql_connector import get_connection
import json

def insert_many_quizzes(quiz_list):
    conn = get_connection()
    inserted = 0
    try:
        with conn.cursor() as cursor:
            for q in quiz_list:
                sql = """
                INSERT INTO quiz (amino_acid, topic, question, options, answer, grade)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    q["아미노산"],
                    q["주제"],
                    q["question"],
                    json.dumps(eval(q["options"])) if isinstance(q["options"], str) else json.dumps(q["options"]),
                    q["answer"],
                    q["학년"]
                ))
                inserted += 1
        conn.commit()
        return inserted
    except Exception as e:
        print("[DB Insert 오류]", e)
        return inserted

def get_quiz_by_id(quiz_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM quiz WHERE id = %s", (quiz_id,))
            quiz = cursor.fetchone()
            if quiz:
                return {"quiz": quiz}, 200
            else:
                return {"error": "해당 ID의 퀴즈가 없습니다."}, 404
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500

def get_quizzes_by_amino_acid(amino_acid):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM quiz WHERE amino_acid = %s ORDER BY id"
            cursor.execute(sql, (amino_acid,))
            quizzes = cursor.fetchall()
            return {"quizzes": quizzes}, 200
    except Exception as e:
        return {"error": f"DB 오류: {str(e)}"}, 500
    finally:
        conn.close()

def insert_quiz_log(user_id: str, chapter: str, question_number: int, status: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
              INSERT INTO quiz_log (user_id, chapter, question_number, status)
              VALUES (%s, %s, %s, %s)
            """, (user_id, chapter, question_number, status))
        conn.commit()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": f"DB 오류: {e}"}, 500
    finally:
        try: conn.close()
        except: pass

def get_quiz_logs_by_user(user_id: str, limit: int = 100):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
              SELECT Progress_id, user_id, chapter, question_number, status, answered_at
              FROM quiz_log
              WHERE user_id=%s
              ORDER BY answered_at DESC, Progress_id DESC
              LIMIT %s
            """, (user_id, limit))
            return cur.fetchall()
    finally:
        try: conn.close()
        except: pass