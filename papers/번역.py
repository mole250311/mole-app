from flask import Flask, request, jsonify
from deep_translator import GoogleTranslator
import requests
import xml.etree.ElementTree as ET
import time
import os
import calendar

app = Flask(__name__)

# ---------- 옵션 ----------
EUTILS_API_KEY = os.getenv("NCBI_API_KEY")   # 있으면 자동 사용
HEADERS = {"User-Agent": "PaperTranslator/1.0 (contact: you@example.com)"}
RATE_LIMIT_SEC = 0.34                         # NCBI 권장 속도
# -------------------------

# 번역 래퍼
def translate(text: str) -> str:
    if not text:
        return ""
    try:
        return GoogleTranslator(source="auto", target="ko").translate(text)
    except Exception as e:
        print(f"[번역 오류] {e}")
        return text  # 실패 시 원문 유지

def parse_pub_date(article_root) -> str:
    """
    PubDate는 형식이 제각각이라 Year/Month/Day, MedlineDate 등을 순서대로 시도
    """
    try:
        pub_date_elem = article_root.find(".//PubDate")
        if pub_date_elem is None:
            return "날짜 정보 없음"

        # 1) 일반 Year/Month/Day 조합
        year = pub_date_elem.findtext("Year", "")
        month_raw = pub_date_elem.findtext("Month", "")
        day = pub_date_elem.findtext("Day", "01")

        # Month 문자열 → 숫자
        month_map = {name: f"{num:02d}" for num, name in enumerate(calendar.month_abbr) if name}
        month = month_map.get((month_raw[:3] if month_raw else "").capitalize(), "01") if month_raw else "01"

        if year:
            return f"{year}-{month}-{day}"

        # 2) MedlineDate (예: "2019 Jan-Feb")
        medline = pub_date_elem.findtext("MedlineDate", "")
        if medline:
            # 가장 앞의 4자리 연도만 추출
            import re
            m = re.search(r"\b(19|20)\d{2}\b", medline)
            if m:
                return f"{m.group(0)}-01-01"
            return medline  # 그래도 안되면 원문 반환

    except Exception as e:
        print(f"[발행일 파싱 오류] {e}")

    return "날짜 정보 없음"

# ---------- 통합 엔드포인트 ----------
@app.route('/papers', methods=['GET'])
def translate_paper():
    """
    통합 버전:
      - query (필수)
      - order=relevance|latest (기본 relevance)
      - limit=1..10 (기본 3)
      - translate=true|false (기본 true)
    응답: 상세 필드 + ko 번역 포함
    """
    query = request.args.get("query")
    order = request.args.get("order", "relevance").lower()   # relevance | latest
    try:
        limit = int(request.args.get("limit", 3))
    except ValueError:
        limit = 3
    limit = max(1, min(limit, 10))  # 과도한 호출 방지

    do_translate = request.args.get("translate", "true").lower() == "true"

    if not query:
        return jsonify({"error": "query parameter required"}), 400

    # 정렬 옵션 매핑
    sort_map = {
        "latest": "pub+date",
        "relevance": "relevance"
    }
    sort_value = sort_map.get(order, "relevance")

    # 1) PMID 검색
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": limit,
        "retmode": "json",
        "sort": sort_value
    }
    if EUTILS_API_KEY:
        search_params["api_key"] = EUTILS_API_KEY

    try:
        r = requests.get(search_url, params=search_params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        id_list = r.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        return jsonify({"error": f"PubMed 검색 오류: {str(e)}"}), 500

    results = []

    # 2) 각 PMID 상세 조회
    for pmid in id_list:
        try:
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
            if EUTILS_API_KEY:
                fetch_params["api_key"] = EUTILS_API_KEY

            fr = requests.get(fetch_url, params=fetch_params, headers=HEADERS, timeout=20)
            fr.raise_for_status()

            root = ET.fromstring(fr.text)
            article = root.find(".//PubmedArticle")
            art_data = article.find(".//Article") if article is not None else None
            if art_data is None:
                continue

            # 제목
            title_en = art_data.findtext("ArticleTitle", default="(No Title)")
            title_ko = translate(title_en) if do_translate else None

            # 초록 (라벨 포함 결합)
            parts = []
            for node in art_data.findall(".//Abstract/AbstractText"):
                label = node.get("Label")
                text = "".join(node.itertext()).strip()
                parts.append(f"{label}: {text}" if label else text)
            abstract_en = " ".join([p for p in parts if p]) if parts else ""
            abstract_ko = translate(abstract_en) if (do_translate and abstract_en) else (None if do_translate else "")

            # 저자
            authors_en, authors_ko = [], []
            for author in art_data.findall(".//Author"):
                first = author.findtext("ForeName")
                last = author.findtext("LastName")
                if first and last:
                    full = f"{first} {last}"
                    authors_en.append(full)
                    if do_translate:
                        try:
                            authors_ko.append(translate(full))
                        except Exception:
                            authors_ko.append(full)

            # 유형
            type_nodes = article.findall(".//PublicationType")
            pub_type = type_nodes[0].text if type_nodes else "유형 없음"

            # 학술지
            journal = art_data.findtext(".//Journal/Title", default="(No Journal)")

            # 발행일
            published = parse_pub_date(article)

            # 페이지
            pages = article.findtext(".//Pagination/MedlinePgn", default="(No Pages)")

            results.append({
                "pmid": pmid,
                "title_en": title_en,
                "title_ko": title_ko,
                "abstract_en": abstract_en,
                "abstract_ko": abstract_ko,
                "authors_en": authors_en,
                "authors_ko": authors_ko if do_translate else None,
                "type": pub_type,
                "journal": journal,
                "published": published,
                "pages": pages,
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })

            time.sleep(RATE_LIMIT_SEC)  # NCBI rate limit

        except Exception as e:
            print(f"[⚠️] PMID {pmid} 처리 중 오류: {e}")
            continue

    return jsonify({
        "query": query,
        "order": order,
        "limit": limit,
        "translate": do_translate,
        "results": results
    })

@app.get("/healthz")
def healthz():
    return {"ok": True}

if __name__ == '__main__':
    app.run(debug=True)
