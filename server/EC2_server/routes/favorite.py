from flask import Blueprint, request, jsonify
from db.favorite.dao import add_favorite, remove_favorite, list_favorites

favorite_bp = Blueprint("favorite", __name__)

@favorite_bp.route("/favorites/add", methods=["POST"])
def favorite_add():
    data = request.get_json(silent=True) or {}
    if not data.get("user_id") or not data.get("chapter_id"):
        return jsonify({"ok": False, "error": "user_id, chapter_id 필요"}), 400
    res, st = add_favorite(data["user_id"], data["chapter_id"])
    return jsonify(res), st

@favorite_bp.route("/favorites/remove", methods=["POST"])
def favorite_remove():
    data = request.get_json(silent=True) or {}
    if not data.get("user_id") or not data.get("chapter_id"):
        return jsonify({"ok": False, "error": "user_id, chapter_id 필요"}), 400
    res, st = remove_favorite(data["user_id"], data["chapter_id"])
    return jsonify(res), st

@favorite_bp.route("/favorites", methods=["GET"])
def favorite_list():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "user_id 필요"}), 400
    rows = list_favorites(user_id)
    items = []
    for r in rows:
        if isinstance(r, dict):
            items.append(r)
        else:
            Favorite_id, user_id, chapter_id = r
            items.append({"favorite_id": Favorite_id, "user_id": user_id, "chapter_id": chapter_id})
    return jsonify({"ok": True, "items": items}), 200