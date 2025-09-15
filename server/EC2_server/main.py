# app.py
from __future__ import annotations
from flask import Flask, request, jsonify
from pathlib import Path
from dotenv import load_dotenv
import route_table

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

# -------- Flask 기본 설정 --------
app.config.update(
    JSON_AS_ASCII=False,             # 한글 유니코드 이스케이프 비활성
    JSONIFY_PRETTYPRINT_REGULAR=False,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 업로드 최대 16MB (필요시 조정)
)

# (옵션) CORS
try:
    from flask_cors import CORS
    CORS(app, resources={r"/*": {"origins": "*"}})  # 필요한 범위로 제한 권장
except Exception:
    pass

# -------- Helper 응답 --------
def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code

def _err(msg: str, code: int, *, error_code: str | None = None, details: dict | None = None):
    body = {"ok": False, "error": msg}
    if error_code:
        body["code"] = error_code
    if details:
        body["details"] = details
    return jsonify(body), code

# -------- 블루프린트 등록 --------
# /model/compose 직접 응답 처리
from routes.model import model_route
app.register_blueprint(model_route, url_prefix="/model")

# /search 직접 응답 처리 (예: /from_name 엔드포인트)
from routes.search import search_route
app.register_blueprint(search_route)

# /paper 직접 응답 처리
# 파일명이 papers.py 라면 아래 import 라인을 변경하세요.
# from routes.papers import paper_route
from routes.paper import paper_route
app.register_blueprint(paper_route, url_prefix="/paper")

# 사용자
from routes.user import user_route
app.register_blueprint(user_route)

# 퀴즈
from routes.quiz import quiz_bp
app.register_blueprint(quiz_bp)

# 공지
from routes.notice import notice_route
app.register_blueprint(notice_route)

# 즐겨찾기
from routes.favorite import favorite_bp
app.register_blueprint(favorite_bp)

# 진행도
from routes.progress import progress_route
app.register_blueprint(progress_route)

# DB/관리자
from routes.admin import admin_route
app.register_blueprint(admin_route)

# -------- 동적 라우팅 설정 (relay) --------
from relay.handler import relay_handler
for route_path in route_table.ROUTE_TABLE.keys():
    # Flask endpoint에는 슬래시가 못 들어가므로 치환
    endpoint_name = f"relay:{route_path}".replace("/", ":")
    app.add_url_rule(
        rule=route_path,
        endpoint=endpoint_name,
        view_func=relay_handler,
        methods=["POST"],
    )

# -------- 전역 에러 핸들러 --------
@app.errorhandler(400)
def bad_request(e):
    return _err("잘못된 요청입니다.", 400, error_code="BAD_REQUEST", details={"reason": str(e)})

@app.errorhandler(404)
def not_found(e):
    return _err("리소스를 찾을 수 없습니다.", 404, error_code="NOT_FOUND")

@app.errorhandler(405)
def method_not_allowed(e):
    return _err("허용되지 않은 메서드입니다.", 405, error_code="METHOD_NOT_ALLOWED")

@app.errorhandler(413)
def request_entity_too_large(e):
    return _err("업로드 용량 제한을 초과했습니다.", 413, error_code="PAYLOAD_TOO_LARGE")

@app.errorhandler(Exception)
def internal_error(e):
    # 필요시 로거에 스택트레이스 기록
    return _err("서버 내부 오류", 500, error_code="INTERNAL_SERVER_ERROR", details={"reason": str(e)})

# -------- 헬스체크 --------
@app.route("/healthz", methods=["GET"])
def healthz():
    return _ok({"ok": True, "status": "healthy"})

# -------- 실행 --------
if __name__ == "__main__":
    # 개발환경: Flask 내장 서버
    app.run(host="0.0.0.0", port=8000, debug=True)

    # 운영 배포 권장:
    # gunicorn -w 4 -k gthread -b 0.0.0.0:8000 app:app --timeout 60
