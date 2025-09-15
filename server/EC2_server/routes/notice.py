# routes/notice.py
from __future__ import annotations
from flask import Blueprint, jsonify
from db.notice.dao import get_all_notices

notice_route = Blueprint("notice", __name__)

# -----------------------
# Helpers
# -----------------------
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
# 공지사항 목록 조회
# -----------------------
@notice_route.route("/notices", methods=["GET"])
def list_notices():
    try:
        rows = get_all_notices()
    except Exception as e:
        return _err("공지사항 조회 실패", 500, error_code="DB_ERROR", details={"reason": str(e)})

    notices = []
    try:
        for r in rows or []:
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
    except Exception as e:
        return _err("공지사항 변환 실패", 500, error_code="PARSE_ERROR", details={"reason": str(e)})

    return _ok({"ok": True, "notices": notices})
