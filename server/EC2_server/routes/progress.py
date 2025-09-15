# routes/progress.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
from db.progress.dao import get_overall, set_overall, ensure_overall_row

progress_route = Blueprint("progress", __name__)

# -----------------------
# Helpers
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
# 전체 진행도 조회
# -----------------------
@progress_route.route("/progress/overall", methods=["GET"])
def overall_get():
    user_id = (request.args.get("user_id") or "").strip()
    if not user_id:
        return _err("user_id 필요", 400, error_code="MISSING_USER_ID")

    # 없으면 생성
    try:
        ensure_overall_row(user_id)
    except Exception as e:
        return _err("초기화 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})

    # 조회
    try:
        row = get_overall(user_id)
    except Exception as e:
        return _err("조회 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})

    # DictCursor/tuple 모두 대응
    if isinstance(row, dict) and row:
        data = {
            "user_id": row.get("user_id", user_id),
            "total_solved": int(row.get("total_solved") or 0),
            "total_progress_percent": float(row.get("total_progress_percent") or 0.0),
        }
    else:
        # tuple 또는 None
        if row:
            uid, total_solved, percent = row
        else:
            uid, total_solved, percent = user_id, 0, 0.0
        data = {
            "user_id": uid,
            "total_solved": int(total_solved or 0),
            "total_progress_percent": float(percent or 0.0),
        }

    return _ok({"ok": True, "overall": data})


# -----------------------
# 전체 진행도 세팅
# -----------------------
@progress_route.route("/progress/overall/set", methods=["POST"])
def overall_set():
    """
    Body:
    { "user_id": "u1", "total_solved": 23, "total_questions": 50 }
    """
    data = _json()
    required = ("user_id", "total_solved", "total_questions")
    if not all(k in data for k in required):
        return _err("user_id, total_solved, total_questions 필요", 400, error_code="MISSING_FIELDS")

    user_id = str(data.get("user_id") or "").strip()
    if not user_id:
        return _err("user_id 필요", 400, error_code="MISSING_USER_ID")

    # 타입 변환 검증
    try:
        total_solved = int(data.get("total_solved"))
        total_questions = int(data.get("total_questions"))
    except Exception:
        return _err("total_solved, total_questions 는 정수여야 합니다.", 400, error_code="INVALID_PARAM")

    try:
        res, st = set_overall(user_id, total_solved, total_questions)
    except Exception as e:
        return _err("설정 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})

    # DAO에서 반환한 상태 매핑
    if st != 200:
        return _err(res.get("error", "설정 실패"), st, error_code="DB_ERROR")

    return _ok({"ok": True, **res})
