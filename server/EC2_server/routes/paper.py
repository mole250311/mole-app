# routes/papers.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
import os, calendar, xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
import requests
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, as_completed

paper_route = Blueprint("papers", __name__)

# ------------------- Config -------------------
HTTP_TIMEOUT = 5
RETMAX_DEFAULT = 5
RETMAX_MAX = 15
EUTILS_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EUTILS_FETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
USER_AGENT = "EduMolecule/1.0 (+papers)"
PUBMED_DB = "pubmed"
NCBI_API_KEY = os.getenv("NCBI_API_KEY")

# 동시 요청 개수 (PubMed 예절상 너무 높이지 말 것)
MAX_WORKERS = int(os.getenv("PAPERS_MAX_WORKERS", "4"))

# ------------------- Requests 세션 (커넥션 재사용) -------------------
_session: Optional[requests.Session] = None
def _get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS, max_retries=0)
        s.mount("https://", adapter)
        s.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        })
        _session = s
    return _session

# ------------------- Helpers -------------------
def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code

def _err(msg: str, code: int, *, error_code: str = None, details: dict | None = None):
    body = {"ok": False, "error": msg}
    if error_code: body["code"] = error_code
    if details: body["details"] = details
    return jsonify(body), code

# ------------------- NLTK 초기화 -------------------
NLTK_DATA_PATH = os.path.expanduser("~/nltk_data")
nltk.data.path = [NLTK_DATA_PATH]
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", download_dir=NLTK_DATA_PATH)

# ------------------- 텍스트 유틸 -------------------
def summarize_abstract(abstract: str, num_sentences: int = 2) -> str:
    try:
        sentences = sent_tokenize(abstract or "")
        if len(sentences) <= num_sentences:
            return abstract or ""
        vec = TfidfVectorizer()
        tf = vec.fit_transform(sentences)
        sim = (tf * tf.T).toarray()
        graph = nx.from_numpy_array(sim)
        scores = nx.pagerank(graph)
        ranked = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
        return " ".join([s for _, s in ranked[:num_sentences]])
    except Exception:
        return abstract or ""

def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    try:
        if not text or len(text.strip()) < 10:
            return []
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        tf = vec.fit_transform([text])
        scores = list(zip(vec.get_feature_names_out(), tf.toarray()[0]))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [w for w, _ in scores[:top_n]]
    except Exception:
        return []

# ------------------- PubMed 호출 -------------------
def _requests_get(url: str, *, params: dict) -> requests.Response:
    s = _get_session()
    return s.get(url, params=params, timeout=HTTP_TIMEOUT)

def fetch_pmids(query: str, retmax: int) -> List[str]:
    params = {"db": PUBMED_DB, "term": query, "retmax": retmax, "retmode": "json"}
    if NCBI_API_KEY: params["api_key"] = NCBI_API_KEY
    try:
        resp = _requests_get(EUTILS_SEARCH, params=params)
    except requests.Timeout:
        raise RuntimeError(("UPSTREAM_TIMEOUT", 408, "PubMed 검색 타임아웃"))
    except requests.RequestException as e:
        raise RuntimeError(("UPSTREAM_NETWORK", 502, f"PubMed 네트워크 오류: {e}"))

    if resp.status_code == 429:
        raise RuntimeError(("RATE_LIMITED", 429, "요청이 너무 많습니다. 잠시 후 다시 시도하세요."))
    if resp.status_code >= 500:
        raise RuntimeError(("UPSTREAM_ERROR", 502, "PubMed 상위 서비스 오류", {"upstream_status": resp.status_code}))
    if resp.status_code != 200:
        raise RuntimeError(("UPSTREAM_BAD_RESPONSE", 502, "PubMed 비정상 응답", {"upstream_status": resp.status_code}))

    try:
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        raise RuntimeError(("UPSTREAM_PARSE_FAILED", 502, f"PubMed 응답 파싱 실패: {e}"))

def fetch_article_xml(pmid: str) -> ET.Element:
    params = {"db": PUBMED_DB, "id": pmid, "retmode": "xml"}
    if NCBI_API_KEY: params["api_key"] = NCBI_API_KEY
    try:
        resp = _requests_get(EUTILS_FETCH, params=params)
    except requests.Timeout:
        raise RuntimeError(("UPSTREAM_TIMEOUT", 408, "PubMed 상세 타임아웃"))
    except requests.RequestException as e:
        raise RuntimeError(("UPSTREAM_NETWORK", 502, f"PubMed 네트워크 오류: {e}"))

    if resp.status_code == 429:
        raise RuntimeError(("RATE_LIMITED", 429, "요청이 너무 많습니다. 잠시 후 다시 시도하세요."))
    if resp.status_code >= 500:
        raise RuntimeError(("UPSTREAM_ERROR", 502, "PubMed 상위 서비스 오류", {"upstream_status": resp.status_code}))
    if resp.status_code != 200:
        raise RuntimeError(("UPSTREAM_BAD_RESPONSE", 502, "PubMed 비정상 응답", {"upstream_status": resp.status_code}))

    try:
        return ET.fromstring(resp.text)
    except Exception as e:
        raise RuntimeError(("UPSTREAM_PARSE_FAILED", 502, f"XML 파싱 실패: {e}"))

# ------------------- 파싱/후처리 -------------------
MONTH_MAP = {name: f"{num:02d}" for num, name in enumerate(calendar.month_abbr) if name}

def parse_article(root: ET.Element, pmid: string) -> Dict[str, Any]:
    article = root.find(".//PubmedArticle")
    art_data = article.find(".//Article") if article is not None else None
    if art_data is None:
        raise ValueError("기사 데이터 없음")

    title_en = art_data.findtext("ArticleTitle", default="(No Title)")
    abstract_nodes = art_data.findall(".//AbstractText")
    abstract_en = " ".join(["".join(n.itertext()).strip() for n in abstract_nodes if n is not None])
    journal = art_data.findtext(".//Journal/Title", default="Unknown Journal")

    pub_date_elem = article.find(".//PubDate") if article is not None else None
    if pub_date_elem is not None:
        year = pub_date_elem.findtext("Year", "")
        month_raw = pub_date_elem.findtext("Month", "")
        day = pub_date_elem.findtext("Day", "01")
    else:
        year, month_raw, day = "", "", "01"
    month = MONTH_MAP.get((month_raw or "")[:3].capitalize(), "01") if month_raw else "01"
    pub_date = f"{year}-{month}-{day}" if year else "Unknown Date"

    authors = []
    for author in art_data.findall(".//Author"):
        first = author.findtext("ForeName")
        last = author.findtext("LastName")
        if first and last:
            authors.append(f"{first} {last}")
    if not authors:
        authors = ["Unknown Author"]

    types = [e.text for e in (article.findall(".//PublicationType") if article is not None else []) if e.text] or ["Unknown Type"]
    pages = article.findtext(".//Pagination/MedlinePgn", default="") if article is not None else ""

    summary = summarize_abstract(abstract_en)
    keywords = extract_keywords(abstract_en)

    return {
        "pmid": pmid,
        "title_en": title_en,
        "abstract_en": abstract_en,
        "summary_en": summary,
        "keywords": keywords,
        "authors": authors,
        "types": types,
        "journal": journal,
        "pub_date": pub_date,
        "pages": pages,
        "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }

# ------------------- 검색 + (옵션) 번역 파이프라인 (병렬) -------------------
def _process_pmid(pmid: str, do_translate: bool) -> Optional[Dict[str, Any]]:
    try:
        root = fetch_article_xml(pmid)
        item = parse_article(root, pmid)
        if do_translate:
            # 번역 비용이 큰 편이므로 제목만 번역(기본). 전체 번역은 쿼리옵션으로.
            item["title_ko"] = GoogleTranslator(source="en", target="ko").translate(item["title_en"])
            # 전체 번역을 원하면 아래 라인 주석 해제 + translate=full 사용
            # item["abstract_ko"] = GoogleTranslator(source="en", target="ko").translate(item["abstract_en"])
        return item
    except Exception as e:
        # 개별 항목 실패는 무시하고 계속
        print(f"[PMID {pmid}] 처리 실패: {e}")
        return None

def search_and_optionally_translate(query: str, retmax: int, translate_mode: str) -> List[Dict[str, Any]]:
    pmids = fetch_pmids(query, retmax)
    if not pmids:
        return []

    do_translate = translate_mode in ("true", "title", "full")
    translate_full = translate_mode == "full"

    items: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_process_pmid, pmid, do_translate): pmid for pmid in pmids}
        for fut in as_completed(futures):
            item = fut.result()
            if item is None:
                continue
            # full 번역 요청 시에만 초록 번역 실행(추가 비용)
            if do_translate and translate_full and "abstract_ko" not in item and item.get("abstract_en"):
                try:
                    item["abstract_ko"] = GoogleTranslator(source="en", target="ko").translate(item["abstract_en"])
                except Exception as e:
                    item["abstract_ko"] = "(번역 실패)"
            items.append(item)
    return items

# ------------------- 엔드포인트 -------------------
@paper_route.route("/papers", methods=["GET"])
def get_papers():
    query = (request.args.get("query") or "").strip()
    if not query:
        return _err("query 파라미터가 필요합니다.", 400, error_code="MISSING_PARAM")

    # retmax 검증
    try:
        retmax = int(request.args.get("retmax", RETMAX_DEFAULT))
        if retmax <= 0 or retmax > RETMAX_MAX:
            return _err("retmax 범위 오류", 400, error_code="INVALID_PARAM", details={"max": RETMAX_MAX})
    except ValueError:
        return _err("retmax는 정수여야 합니다.", 400, error_code="INVALID_PARAM")

    # 번역 모드: false(번역 없음/기본), title(제목만), full(제목+초록), true=title과 동일
    translate_mode = (request.args.get("translate", "false").lower())
    if translate_mode not in ("false", "true", "title", "full"):
        return _err("translate 파라미터는 false|true|title|full", 400, error_code="INVALID_PARAM")

    try:
        papers = search_and_optionally_translate(query=query, retmax=retmax, translate_mode=translate_mode)
        return _ok({"ok": True, "query": query, "count": len(papers), "papers": papers})
    except RuntimeError as re:
        code, http, msg, *rest = re.args[0] if isinstance(re.args[0], tuple) else ("UPSTREAM_ERROR", 502, str(re))
        details = rest[0] if rest else None
        return _err(msg, http, error_code=code, details=details)
    except Exception as e:
        return _err("알 수 없는 오류", 500, error_code="UNKNOWN_ERROR", details={"reason": str(e)})
