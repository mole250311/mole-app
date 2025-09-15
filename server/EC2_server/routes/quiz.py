# routes/quiz.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
import json
import pandas as pd

from db.quiz.dao import (
    insert_many_quizzes, get_quiz_by_id, get_quizzes_by_amino_acid,
    get_total_quiz_count, insert_quiz_log, get_quiz_logs_by_user
)
from db.progress.dao import update_overall_increment

quiz_bp = Blueprint("quiz", __name__)

# -----------------------
# Helper
# -----------------------
def _json():
    return request.get_json(silent=True) or {}

def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code

def _err(msg: str, code: int, *, error_code: str = None, details: dict | None = None):
    body = {"ok": False, "error": msg}
    if error_code: body["code"] = error_code
    if details: body["details"] = details
    return jsonify(body), code


# -----------------------
# 퀴즈 파일 업로드
# -----------------------
@quiz_bp.route("/quizzes/upload", methods=["POST"])
def upload_quiz_file():
    if "file" not in request.files:
        return _err("파일이 포함되지 않았습니다.", 400, error_code="MISSING_FILE")

    file = request.files["file"]
    try:
        if file.filename.endswith(".json"):
            quiz_list = json.load(file)
        elif file.filename.endswith(".csv"):
            df = pd.read_csv(file)
            quiz_list = df.to_dict(orient="records")
        else:
            return _err("지원되지 않는 파일 형식 (CSV 또는 JSON만 가능)", 400, error_code="INVALID_FILE_TYPE")

        result, status = insert_many_quizzes(quiz_list)
        if status != 200:
            return _err(result.get("error","DB 오류"), status, error_code="DB_ERROR")

        return _ok({"ok": True, "inserted": result["inserted"]})
    except Exception as e:
        return _err("파일 처리 중 오류 발생", 500, error_code="UPLOAD_FAILED", details={"reason": str(e)})


# -----------------------
# 퀴즈 단건 조회
# -----------------------
@quiz_bp.route("/quizzes/<int:quiz_id>", methods=["GET"])
def get_quiz_by_id_route(quiz_id):
    result, status = get_quiz_by_id(quiz_id)
    if status == 404:
        return _err("퀴즈를 찾을 수 없습니다.", 404, error_code="NOT_FOUND")
    if status != 200:
        return _err("퀴즈 조회 실패", 500, error_code="DB_ERROR")
    return _ok({"ok": True, "quiz": result["quiz"]})


# -----------------------
# 특정 아미노산 퀴즈 목록 조회
# -----------------------
@quiz_bp.route("/quizzes", methods=["GET"])
def get_quizzes_by_amino_acid_route():
    amino_acid = request.args.get("amino_acid","").strip()
    if not amino_acid:
        return _err("amino_acid 파라미터가 필요합니다.", 400, error_code="MISSING_PARAM")

    result, status = get_quizzes_by_amino_acid(amino_acid)
    if status != 200:
        return _err(result.get("error","DB 오류"), 500, error_code="DB_ERROR")
    return _ok({"ok": True, "quizzes": result["quizzes"]})


# -----------------------
# 퀴즈 로그 + 전체 진행도 갱신
# -----------------------
@quiz_bp.route("/quiz/log", methods=["POST"])
def quiz_log_and_overall():
    data = _json()
    user_id = str(data.get("user_id","")).strip()
    status = (data.get("status") or "").lower()  # 'correct' | 'wrong'

    if not user_id or status not in ("correct","wrong"):
        return _err("user_id, status(correct|wrong) 필요", 400, error_code="MISSING_FIELDS")

    # 1) 개별 로그 저장
    try:
        insert_quiz_log(
            user_id=user_id,
            chapter=data.get("amino_acid"),
            quiz_id=int(data.get("quiz_id") or 0),
            status=status
        )
    except Exception as e:
        # 로그 실패는 치명적이지 않음
        print("[quiz_log] failed:", e)

    # 2) 전체 진행도 갱신
    try:
        total_quizzes = get_total_quiz_count()
        solved_delta = 1 if status == "correct" else 0
        res, st = update_overall_increment(user_id, solved_delta, total_quizzes)
        if st != 200:
            return _err(res.get("error","진행도 갱신 실패"), st, error_code="DB_ERROR")
        return _ok(res)
    except Exception as e:
        return _err("진행도 갱신 실패", 500, error_code="PROGRESS_UPDATE_FAILED", details={"reason": str(e)})


# -----------------------
# 유저 퀴즈 로그 조회
# -----------------------
@quiz_bp.route("/quiz/logs/<user_id>", methods=["GET"])
def fetch_quiz_logs(user_id: str):
    try:
        limit = int(request.args.get("limit", 100))
        logs = get_quiz_logs_by_user(user_id, limit)
        return _ok({"ok": True, "logs": logs})
    except ValueError:
        return _err("limit은 정수여야 합니다.", 400, error_code="INVALID_PARAM")
    except Exception as e:
        return _err("조회 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})
