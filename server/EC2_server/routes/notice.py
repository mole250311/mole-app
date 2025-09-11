from flask import Blueprint, jsonify
from db.notice.dao import get_all_notices

notice_route = Blueprint("notice", __name__)

@notice_route.route("/notices", methods=["GET"])
def list_notices():
    try:
        rows = get_all_notices()
        # DictCursor 아닌 경우 tuple이라면 dict로 변환
        notices = []
        for r in rows:
            if isinstance(r, dict):
                notices.append(r)
            else:
                notice_id, title, content, created_at = r
                notices.append({
                    "notice_id": notice_id,
                    "title": title,
                    "content": content,
                    "created_at": str(created_at)
                })
        return jsonify({"ok": True, "notices": notices}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500