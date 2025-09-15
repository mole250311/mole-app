# routes/favorite.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
from db.favorite.dao import add_favorite, remove_favorite, list_favorites

favorite_bp = Blueprint("favorite", __name__)

# -----------------------
# Helpers
# -----------------------
def _json():
    return request.get_json(silent=True) or {}

def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code

def _err(msg: str, code: int, *, error_code: str = None, details: dict | None = None):
    body = {"ok": False, "error": msg}
    if error_code:
        body["code"] = error_code
    if details:
        body["details"] = details
    return jsonify(body), code


# -----------------------
# 즐겨찾기 추가
# -----------------------
@favorite_bp.route("/favorites/add", methods=["POST"])
def favorite_add():
    data = _json()
    user_id = str(data.get("user_id", "")).strip()
    chapter_id = str(data.get("chapter_id", "")).strip()

    if not user_id or not chapter_id:
        return _err("user_id, chapter_id 필요", 400, error_code="MISSING_FIELDS")

    try:
        res, st = add_favorite(user_id, chapter_id)
    except Exception as e:
        return _err("즐겨찾기 추가 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})

    # 중복 추가를 409로 매핑(DAO가 메시지를 제공하면 감지)
    if st != 200:
        msg = res.get("error", "DB 오류")
        if "duplicate" in msg.lower() or "unique" in msg.lower():
            return _err("이미 즐겨찾기에 존재합니다.", 409, error_code="DUPLICATE_FAVORITE")
        return _err(msg, st, error_code="DB_ERROR")

    return _ok({"ok": True, "message": "즐겨찾기에 추가되었습니다."})


# -----------------------
# 즐겨찾기 제거
# -----------------------
@favorite_bp.route("/favorites/remove", methods=["POST"])
def favorite_remove():
    data = _json()
    user_id = str(data.get("user_id", "")).strip()
    chapter_id = str(data.get("chapter_id", "")).strip()

    if not user_id or not chapter_id:
        return _err("user_id, chapter_id 필요", 400, error_code="MISSING_FIELDS")

    try:
        res, st = remove_favorite(user_id, chapter_id)
    except Exception as e:
        return _err("즐겨찾기 제거 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})

    if st != 200:
        return _err(res.get("error", "DB 오류"), st, error_code="DB_ERROR")

    return _ok({"ok": True, "message": "즐겨찾기에서 제거되었습니다."})


# -----------------------
# 즐겨찾기 목록
# -----------------------
@favorite_bp.route("/favorites", methods=["GET"])
def favorite_list():
    uid = str(request.args.get("user_id", "")).strip()
    if not uid:
        return _err("user_id 필요", 400, error_code="MISSING_USER_ID")

    try:
        rows = list_favorites(uid)
    except Exception as e:
        return _err("즐겨찾기 조회 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})

    items = []
    try:
        for r in rows or []:
            if isinstance(r, dict):
                # 키 이름 표준화: favorite_id 소문자 키로 통일
                fid = r.get("Favorite_id") or r.get("favorite_id")
                items.append({
                    "favorite_id": fid,
                    "user_id": r.get("user_id"),
                    "chapter_id": r.get("chapter_id"),
                })
            else:
                # tuple 형태: (Favorite_id, user_id, chapter_id)
                Favorite_id, user_id_val, chapter_id_val = r
                items.append({
                    "favorite_id": Favorite_id,
                    "user_id": user_id_val,
                    "chapter_id": chapter_id_val,
                })
    except Exception as e:
        return _err("결과 변환 실패", 500, error_code="PARSE_ERROR", details={"reason": str(e)})

    return _ok({"ok": True, "items": items})
