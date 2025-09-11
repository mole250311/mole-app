from flask import Flask, request, jsonify
from relay.handler import relay_handler
import route_table
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
app = Flask(__name__)
# --------------------
# /model/compose 직접 응답 처리
# --------------------
from routes.model import model_route
app.register_blueprint(model_route, url_prefix="/model")

#--------------------
# /model/search 직접 응답 처리
# -------------------
from routes.search import search_route
app.register_blueprint(search_route)

# --------------------
# /paper 직접응답처리
# -------------------
from routes.paper import paper_route
app.register_blueprint(paper_route, url_prefix="/paper")

from routes.user import user_route
app.register_blueprint(user_route)

# ------------------
# db/quiz 처리
# ------------------
from routes.quiz import quiz_bp
app.register_blueprint(quiz_bp)

# --------------------
# db/notice 처리
# --------------------
from routes.notice import notice_route
app.register_blueprint(notice_route)

# --------------------
# 즐겨찾기 처리
# --------------------
from routes.favorite import favorite_bp
app.register_blueprint(favorite_bp)

# -------------------
# 진행도 처리
# -------------------
from routes.progress import progress_route
app.register_blueprint(progress_route)

# --------------------
# 동적 라우팅 설정
# --------------------
for route_path in route_table.ROUTE_TABLE.keys():
    app.add_url_rule(
        rule=route_path,
        endpoint=route_path,
        view_func=relay_handler,
        methods=["POST"]
    )

# ---------------------------
# db 쿼리 실행
# ---------------------
from routes.admin import admin_route
app.register_blueprint(admin_route)

# --------------------
# 실행
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
