from flask import Blueprint, request, jsonify
from db.progress.dao import get_overall, set_overall, ensure_overall_row

progress_route = Blueprint("progress", __name__)

@progress_route.route("/progress/overall", methods=["GET"])
def overall_get():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "user_id 필요"}), 400
    ensure_overall_row(user_id)
    row = get_overall(user_id)
    if isinstance(row, dict):
        data = row
    else:
        user_id, total_solved, percent = row if row else (user_id, 0, 0.0)
        data = {"user_id": user_id, "total_solved": int(total_solved or 0), "total_progress_percent": float(percent or 0.0)}
    return jsonify({"ok": True, "overall": data}), 200

@progress_route.route("/progress/overall/set", methods=["POST"])
def overall_set():
    """
    Body:
    { "user_id":"u1", "total_solved": 23, "total_questions": 50 }
    """
    data = request.get_json(silent=True) or {}
    if not all(k in data for k in ("user_id","total_solved","total_questions")):
        return jsonify({"ok": False, "error": "user_id, total_solved, total_questions 필요"}), 400
    res, st = set_overall(data["user_id"], int(data["total_solved"]), int(data["total_questions"]))
    return jsonify(res), st