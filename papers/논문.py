# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from deep_translator import GoogleTranslator
import requests
from requests.adapters import HTTPAdapter
import xml.etree.ElementTree as ET
import os
import calendar
import re
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# ---------- 옵션 ----------
EUTILS_API_KEY = os.getenv("NCBI_API_KEY")   # 있으면 자동 사용
HEADERS = {
    "User-Agent": "PaperTranslator/1.0 (contact: you@example.com)",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}
DEFAULT_LIMIT = 3
MAX_LIMIT = 10
TRANSLATE_MAX_WORKERS = int(os.getenv("TRANSLATE_MAX_WORKERS", "6"))  # 병렬 번역 워커 수
# -------------------------

# ---------- HTTP 세션 (Keep-Alive + 풀링 + 재시도) ----------
session = requests.Session()
session.headers.update(HEADERS)
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
session.mount("https://", adapter)
session.mount("http://", adapter)
# -----------------------------------------------------------

# ---------- (A) 번역 캐시 ----------
@lru_cache(maxsize=2048)
def _translate_cached_ko(text: str) -> str:
    return GoogleTranslator(source="auto", target="ko").translate(text)

def translate(text: str) -> str:
    if not text:
        return ""
    try:
        return _translate_cached_ko(text)
    except Exception as e:
        print(f"[번역 오류] {e}")
        return text

def translate_many(texts, do_translate: bool):
    if not do_translate or not texts:
        return [None] * len(texts)
    sep = "\n<§>\n"
    blob = sep.join(t or "" for t in texts)
    out = translate(blob)
    parts = out.split(sep)
    if len(parts) != len(texts):
        return [translate(t) for t in texts]
    return parts

# ---------- 발행일 파싱 ----------
def parse_pub_date(article_root) -> str:
    try:
        pub_date_elem = article_root.find(".//PubDate")
        if pub_date_elem is None:
            return "날짜 정보 없음"

        year = pub_date_elem.findtext("Year", "")
        month_raw = pub_date_elem.findtext("Month", "")
        day = pub_date_elem.findtext("Day", "01")

        month_map = {name: f"{num:02d}" for num, name in enumerate(calendar.month_abbr) if name}
        month = month_map.get((month_raw[:3] if month_raw else "").capitalize(), "01") if month_raw else "01"

        if year:
            return f"{year}-{month}-{day}"

        medline = pub_date_elem.findtext("MedlineDate", "")
        if medline:
            m = re.search(r"\b(19|20)\d{2}\b", medline)
            if m:
                return f"{m.group(0)}-01-01"
            return medline
    except Exception as e:
        print(f"[발행일 파싱 오류] {e}")

    return "날짜 정보 없음"

# ---------- (B) efetch 배치 결과 캐시 ----------
@lru_cache(maxsize=256)
def _efetch_xml(ids_key: str, with_key: bool) -> str:
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {"db": "pubmed", "id": ids_key, "retmode": "xml"}
    if with_key and EUTILS_API_KEY:
        fetch_params["api_key"] = EUTILS_API_KEY
    fr = session.get(fetch_url, params=fetch_params, timeout=30)
    fr.raise_for_status()
    return fr.text

# ---------- 논문 파싱 ----------
def parse_article(article):
    art_data = article.find(".//Article")
    if art_data is None:
        return None

    title_en = art_data.findtext("ArticleTitle", default="(No Title)")

    parts = []
    for node in art_data.findall(".//Abstract/AbstractText"):
        label = node.get("Label")
        text = "".join(node.itertext()).strip()
        parts.append(f"{label}: {text}" if label else text)
    abstract_en = " ".join(p for p in parts if p) if parts else ""

    authors_en = []
    for author in art_data.findall(".//Author"):
        first = author.findtext("ForeName")
        last = author.findtext("LastName")
        if first and last:
            authors_en.append(f"{first} {last}")

    type_nodes = article.findall(".//PublicationType")
    pub_type = type_nodes[0].text if type_nodes else "유형 없음"
    journal = art_data.findtext(".//Journal/Title", default="(No Journal)")
    published = parse_pub_date(article)
    pages = article.findtext(".//Pagination/MedlinePgn", default="(No Pages)")
    pmid = article.findtext(".//PMID")

    return {
        "pmid": pmid,
        "title_en": title_en,
        "abstract_en": abstract_en,
        "authors_en": authors_en,
        "type": pub_type,
        "journal": journal,
        "published": published,
        "pages": pages,
        "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }

# ---------- 단일 논문 번역 ----------
def translate_one(item, do_translate: bool):
    if do_translate:
        title_ko = translate(item["title_en"])
        abstract_ko = translate(item["abstract_en"]) if item["abstract_en"] else ""
        authors_ko = translate_many(item["authors_en"], True)
    else:
        title_ko = None
        abstract_ko = None if item["abstract_en"] else ""
        authors_ko = None

    return {
        "pmid": item["pmid"],
        "title_en": item["title_en"],
        "title_ko": title_ko,
        "abstract_en": item["abstract_en"],
        "abstract_ko": abstract_ko,
        "authors_en": item["authors_en"],
        "authors_ko": authors_ko,
        "type": item["type"],
        "journal": item["journal"],
        "published": item["published"],
        "pages": item["pages"],
        "link": item["link"],
    }

# ---------- 엔드포인트 ----------
@app.route('/papers', methods=['GET'])
def translate_paper():
    query = request.args.get("query")
    order = request.args.get("order", "relevance").lower()

    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
    except ValueError:
        limit = DEFAULT_LIMIT
    limit = max(1, min(limit, MAX_LIMIT))

    do_translate = request.args.get("translate", "false").lower() == "true"

    if not query:
        return jsonify({"error": "query parameter required"}), 400

    sort_map = {"latest": "pub+date", "relevance": "relevance"}
    sort_value = sort_map.get(order, "relevance")

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
        r = session.get(search_url, params=search_params, timeout=15)
        r.raise_for_status()
        id_list = r.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        return jsonify({"error": f"PubMed 검색 오류: {str(e)}"}), 500

    if not id_list:
        return jsonify({
            "query": query,
            "order": order,
            "limit": limit,
            "translate": do_translate,
            "results": []
        })

    ids_key = ",".join(id_list)
    try:
        xml_text = _efetch_xml(ids_key, bool(EUTILS_API_KEY))
        root = ET.fromstring(xml_text)
    except Exception as e:
        return jsonify({"error": f"PubMed 상세 조회 오류: {e}"}), 500

    parsed_items = []
    for article in root.findall(".//PubmedArticle"):
        item = parse_article(article)
        if item:
            parsed_items.append(item)

    results = [None] * len(parsed_items)
    if do_translate and parsed_items:
        max_workers = max(1, min(TRANSLATE_MAX_WORKERS, len(parsed_items)))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {}
            for idx, item in enumerate(parsed_items):
                fut = ex.submit(translate_one, item, True)
                futures[fut] = idx
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results[idx] = fut.result()
                except Exception as e:
                    print(f"[⚠️] 번역 병렬 작업 오류: {e}")
                    base = parsed_items[idx]
                    results[idx] = translate_one(base, False)
    else:
        for i, item in enumerate(parsed_items):
            results[i] = translate_one(item, False)

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
    app.run(host="0.0.0.0", port=8000, debug=True)
