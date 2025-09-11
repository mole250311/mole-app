~~~shell
EC2_server/
├── main.py                    # Flask 실행 진입점
├── requirements.txt           # Python 패키지 목록
├── route_table.py             # 라우트 테이블 (동적 매핑):서버 내부에 처리불가한 모듈을 서버외부에서 처리하고 그 모듈로 중계
├── .env                       # 환경변수 파일: 이메일 전송 정보
├── .gitattributes             # Git 속성 설정
│
├── relay/                     # 요청 중계/핸들러
│   └── handler.py
│
├── routes/                    # API 라우팅 모듈 (Flask Blueprint): 서버 내부 처리 가능한 기능 수행
│   ├── admin.py               # DB관리자 API
│   ├── notice.py              # 공지사항 API
│   ├── user.py                # 사용자 계정 관리 API
│   ├── favorite.py            # 즐겨찾기 API
│   ├── progress.py            # 진행도/학습현황 API
│   ├── quiz.py                # 퀴즈 API
│   ├── model.py               # 3D 모델 검색 API
│   ├── paper.py               # 논문 검색/번역 API
│   └── search.py              # 분자 모델 검색 API
│
├── db/                        # 데이터베이스 관련 DAO & 설정
│   ├── config.py              # DB 설정값 (config)
│   ├── mysql_connector.py     # MySQL 연결 모듈
│   ├── auth/                  # 인증 관련 DAO: 이메일 인증
│   │   └── dao.py
│   ├── favorite/              # 즐겨찾기 DAO: 사용자가 앱에서 설정한 퀴즈 즐겨찾기 정보
│   │   └── dao.py
│   ├── notice/                # 공지사항 DAO: 관리자가 직접 입력한 공지사항
│   │   └── dao.py
│   ├── progress/              # 퀴즈 진행도/학습현황 DAO: 앱 종료 시점에 사용자의 퀴즈 진행도
│   │   └── dao.py
│   ├── quiz/                  # 퀴즈 DAO: 퀴즈 호출
│   │   └── dao.py
│   └── user/                  # 사용자 DAO: 회원가입/회원탈퇴/로그인 등의 회원 계정 관련 
│       └── dao.py
│
└── utils/                     # 공용 유틸리티
    ├── email.py               # 이메일 전송 기능
    └── security.py            # 보안/비밀번호 해시 관련
~~~
