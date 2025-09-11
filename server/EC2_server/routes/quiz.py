from flask import Blueprint, request, jsonify
import json
from db.quiz.dao import insert_many_quizzes,get_quiz_by_id, get_quizzes_by_amino_acid, insert_quiz_log
from db.progress.dao import update_overall_increment

quiz_bp = Blueprint("quiz", __name__)

@quiz_bp.route("/quizzes/upload", methods=["POST"])
def upload_quiz_file():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 포함되지 않았습니다."}), 400

    file = request.files['file']

    try:
        if file.filename.endswith('.json'):
            quiz_list = json.load(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            quiz_list = df.to_dict(orient="records")
        else:
            return jsonify({"error": "지원되지 않는 파일 형식입니다. (CSV 또는 JSON만 가능)"}), 400

        count = insert_many_quizzes(quiz_list)
        return jsonify({"message": f"{count}개의 퀴즈가 저장되었습니다."}), 200

    except Exception as e:
        return jsonify({"error": f"처리 중 오류 발생: {str(e)}"}), 500



@quiz_bp.route("/quizzes/<int:quiz_id>", methods=["GET"])
def get_quiz_by_id_route(quiz_id):
    result, status = get_quiz_by_id(quiz_id)
    return jsonify(result), status



@quiz_bp.route("/quizzes", methods=["GET"])
def get_quizzes_by_amino_acid_route():
    amino_acid = request.args.get("amino_acid")
    if not amino_acid:
        return jsonify({"error": "amino_acid 파라미터가 필요합니다."}), 400

    result, status = get_quizzes_by_amino_acid(amino_acid)
    return jsonify(result), status


@quiz_bp.route("/quiz/log", methods=["POST"])
def quiz_log_and_overall():
    """
    Body 예시:
    {
      "user_id": "u1",
      "amino_acid": "Leucine",         # 선택(있으면 로그에 저장)
      "quiz_id": 12,                   # 선택(있으면 로그에 저장)
      "question_number": 3,            # 선택
      "status": "correct" | "wrong",   # 필수
      "total_questions": 50            # 필수: 전체 문항 수(진행도 % 계산용)
    }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    status = (data.get("status") or "").lower()
    total_questions = data.get("total_questions")

    if not user_id or status not in ("correct", "wrong") or total_questions is None:
        return jsonify({"ok": False, "error": "user_id, status(correct|wrong), total_questions 필요"}), 400

    # 1) (선택) 개별 로그 저장
    try:
        if 'insert_quiz_log' in globals():
            insert_quiz_log(
                user_id=user_id,
                chapter=data.get("amino_acid"),
                question_number=int(data.get("question_number") or 0),
                status=status,
                quiz_id=int(data.get("quiz_id") or 0)
            )
    except Exception as e:
        # 로그 저장 실패해도 진행도 갱신은 시도할 수 있게 분리
        print("[quiz_log] failed to insert log:", e)

    # 2) 전체 진행도 갱신(정답만 +1)
    solved_delta = 1 if status == "correct" else 0
    try:
        res, st = update_overall_increment(user_id, solved_delta, int(total_questions))
        return jsonify(res), st
    except Exception as e:
        return jsonify({"ok": False, "error": f"진행도 갱신 실패: {e}"}), 500