
# PubMed 논문 검색 및 번역 API 서버

## 1. 프로젝트 개요 (Overview)

이 프로젝트는 **PubMed 논문 검색 및 한국어 번역 기능**을 제공하는 NLP API 서버입니다.  
사용자는 키워드 기반으로 논문을 검색하고, 초록 요약 또는 전체 논문 정보를 한국어로 번역할 수 있습니다.  
Flask 기반 서버로 구현되어 있으며, 웹/앱과 쉽게 연동 가능합니다.

## 2. 주요 기능 (Features)

- **논문 검색**: 사용자가 제공한 키워드(query)를 기반으로 PubMed 데이터베이스에서 논문을 검색합니다.
- **상세 정보 조회**: 검색된 논문들의 PMID를 이용하여 제목, 초록, 저자, 발행일, 학술지 등 상세 정보를 가져옵니다.
- **한국어 번역**: 논문 제목, 초록, 저자 등 모든 항목을 한국어로 번역합니다.
- **정렬 옵션**: 검색 결과를 관련성(`relevance`) 또는 최신순(`latest`)으로 정렬 가능.
- **검색 결과 수 제한**: 한 번에 가져올 논문 개수를 1~10개로 조절 가능.
- **API 키 지원**: NCBI E-utilities API 키(`NCBI_API_KEY`)를 환경 변수로 설정 가능.

## 3. 프로젝트 구조 및 파일 설명

~~~shell
pubmed_translation_api/
├── 📁 app/
│   ├── 📜 논문.py           # PubMed 검색, 초록 요약, 키워드 추출 기능
│   └── 📜 번역.py           # 논문 제목/초록/저자 등 한국어 번역
├── 📁 utils/
│   └── 📜 helper.py         # 공통 유틸 함수 (HTTP 요청, 캐싱 등)
├── 📁 tests/
│   └── 📜 test_api.py       # API 기능 테스트
├── 📜 .env                  # 환경 변수 (API 키 등)
└── 📜 README.md             # 프로젝트 설명서
~~~

### 코드 기능 설명

- **`논문.py`**
  - PubMed에서 논문 정보 검색
  - 논문 초록 요약 (TextRank 기반)
  - 키워드 추출
  - 검색 → 요약 → 번역까지 파이프라인 구성 가능

- **`번역.py`**
  - 논문 제목, 초록, 저자, 학술지, 발행일 등 모든 항목 한국어 번역
  - 다중 문장 동시 번역 지원
  - `논문.py`와 함께 사용하여 검색 → 요약 → 번역까지 연계 가능

- **`utils/helper.py`**
  - HTTP 세션 관리
  - 번역 캐싱(lru_cache) 적용
  - 병렬 처리(ThreadPoolExecutor) 지원

## 4. 주요 기술 (Tech Stack)

- **Backend**: Flask
- **HTTP 요청**: requests
- **번역**: deep-translator (Google Translate)
- **병렬 처리**: concurrent.futures.ThreadPoolExecutor
- **데이터 처리**: Python standard library

## 5. API 사용법 (How to Run)

### 엔드포인트

#### `GET /papers`

논문 검색 및 번역 결과를 JSON으로 반환합니다.

**Query Parameters**

| 매개변수      | 필수 여부 | 설명                                                      | 기본값      |
| :------------ | :------- | :-------------------------------------------------------- | :---------- |
| `query`       | **필수** | 검색할 논문 키워드                                        | `(없음)`    |
| `order`       | 선택     | 검색 결과 정렬 기준 (`relevance` 또는 `latest`)           | `relevance` |
| `limit`       | 선택     | 가져올 논문 개수 (1~10)                                  | `3`         |
| `translate`   | 선택     | 논문 내용을 한국어로 번역할지 여부 (`true`/`false`)      | `false`     |

**응답 예시 (JSON)**

~~~json
{
  "query": "검색 키워드",
  "order": "정렬 기준",
  "limit": "결과 개수",
  "translate": "번역 여부",
  "results": [
    {
      "pmid": "PMID",
      "title_en": "영어 제목",
      "title_ko": "한국어 번역 제목",
      "abstract_en": "영어 초록",
      "abstract_ko": "한국어 번역 초록",
      "authors_en": ["저자 1", "저자 2"],
      "authors_ko": ["번역된 저자 1", "번역된 저자 2"],
      "type": "논문 유형",
      "journal": "학술지",
      "published": "발행일 (YYYY-MM-DD)",
      "pages": "페이지",
      "link": "PubMed 링크"
    }
  ]
}
~~~

> `title_ko`, `abstract_ko`, `authors_ko`는 `translate=true`일 경우에만 포함됩니다.

## 6. 설치 및 실행 방법

1. **환경 변수 설정**
~~~bash
export NCBI_API_KEY=your_api_key_here
~~~

2. **의존성 설치**
~~~bash
pip install Flask requests deep-translator
~~~

3. **서버 실행**
~~~bash
python app/main.py
~~~
또는
~~~bash
flask run
~~~

4. **API 테스트**
- 브라우저에서 `http://127.0.0.1:5000/papers?query=example` 접속
- 또는 Postman 등으로 쿼리 테스트 가능
