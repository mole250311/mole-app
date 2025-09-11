# 화학구조 시뮬레이터 ! MOLE
마이크로스톤에서 사용한 유니티와 그 외 것들의 설명! 
## 프로젝트 소개 
이현우 같은 화학 알못들이나 화학을 배우고 싶은 친구들에게 보다 직관적으로 배우기 쉽게 만들기 위해서 만든 3D시뮬레이터 분자구조 애플리케이션!
## 개발 기간
2025-03.?? ~ 2025.10.?? ~~
## 개발자 소개 
김홍경: 

임소현:

이현우: 우리팀 대표 싸가지 현우는 싸가지가 없어 

조현우: 

주성준: 

황예지: 

최예인: 

윤정우:

## 개발환경
개인 노트북/ 데스크탑 

용도: 코드 작성 및 실행

버전: Window10/11, macOS 14.5, macOS 15.5

SW: Unity, Pycharm, Visual Studio, Visual Studio Code, MYSQL, SQLite, PyTorch

운영환경: AWS

프로그래밍 언어: C#, Python

## 시스템 구성도

사진 사진 사진

## 튜툐리얼

1) TutorialManager.cs
   
   Awke()를 통해서 싱글톤설정, 중복생성 방지

   Start()에서 PlayerPrefs.GetInt("TutorialCheck") == 0일 때만 시작

   update()에서 오버레이가 켜져있을 때만 실행

   if (!overlayPanel.activeSelf) return;
   if (Input.GetMouseButtonDown(0)) { ... }

유저는 7,8 등의 주기에서 행동을 멈추는데 Notify라는 트리거를 발동시키면 정지해제하고 코드 실행 

Start()	PlayerPrefs("TutorialCheck")==0일 때 0단계부터 시작(ShowStep)

Update()	오버레이 활성 시 좌클릭 감지 → 오버레이 영역 내부 클릭이면 단계 진행 로직 수행

• 현재 단계가 waitForActionSteps에 있으면 오버레이 끄고 waitingForTrigger=true

• 아니면 step++ 후 마지막이면 EndTutorial(), 아니면 ShowStep()

Notify(string trigger)	행동 대기 중(waitingForTrigger==true) 특정 단계에서 지정 트리거 수신 시 step++ 후 ShowStep()

ShowStep()	모든 stepPanels 중 현재 단계만 활성화. 오버레이 켜고 waitingForTrigger=false

NextFunctionStep()	외부 버튼 등으로 수동 다음 단계. 마지막이면 EndTutorial()

EndTutorial()	오버레이/패널 전부 비활성화, PlayerPrefs("TutorialCheck")=1 저장(다음 실행부터 스킵)

SkipTutorial()	튜토리얼 즉시 종료(EndTutorial)

CurrentStep (getter)	현재 단계 인덱스 반환

## 배경음악 및 클릭음
1) SendManager.cs

   이 스크립트는 앱 전체의 BGM/효과음을 관리하는 싱글톤임

   DontDestoryOnLoad로 인해 씬이 바뀌어도 살아지지 않음

   OnSceneLoaded(Scene scene, LoadSceneMode mode)를 통해 씬에 진입하는순간 BGM 시작

   PlayClickSound()를통해 효과음이 소리나오게 조절

   ToggleBGM(bool on)를 통해 뒤에나오는 토글버튼 조절

   2)SoundManagerBootstrap.cs

 위 스크립트를 통해 씬 마다 두개이상의 노래가 나오지 않게 막음 

 ## 리서치(논문검색)
함수명	동작 설명
Start()	버튼 이벤트 연결 (검색 버튼, 최신순/관련도순 버튼, 뒤로가기 버튼)

Update()	ESC 키 입력 시 Thesis_main 패널이 열려 있으면 홈 화면(OnBackToHome)으로 전환

OnSearchDefault()	기본 검색(관련도순). 검색어 입력값 확인 후 FetchPapers(keyword, "relevance") 코루틴 실행

OnSearchLatest()	최신순 검색. 검색어 입력값 확인 후 FetchPapers(keyword, "latest") 실행

OnSearchRelevance()	관련도순 검색. (Default와 동일하지만 버튼별로 분리 구현)

OnBackToHome()	- 모든 코루틴 중지

- 기존 생성된 논문 카드 오브젝트 삭제
  
- 입력 초기화(선택)
  
- 패널 전환: Main/Detail → Home.
  
HomeSearchBtn()	홈 화면에서 바로 검색 실행. → 패널 전환(Home → Main) + 기본 검색(FetchPapers)

IEnumerator FetchPapers(string keyword, string order)	- 서버 API 요청 (UnityWebRequest)

- 응답 JSON 파싱(PaperResponse)
  
- 논문 리스트(results or papers) 가져오기
  
- 기존 카드 삭제 후 Prefab(cardPrefab) 생성
  
- 각 카드 UI(TMP_Text)에 논문 제목/초록/링크 표시
  
- 검색어 하이라이트 처리
  
TruncateText(string text, int maxLength)	

HighlightKeyword(string text, string keyword, string colorHex = "#007BFF")
 

### 기능
PubMed E- utilities API (esearch/efetch) 를 이용하여 키워드 기반 검색


## 설정 
1. 알림패널
   
toggle : Toggle	토글 UI

background : Image	토글 배경 이미지(색상 전환)

handle : RectTransform	토글 손잡이 위치 전환

handleImage : Image	손잡이 스프라이트 전환

onColor/offColor : Color	켜짐/꺼짐 배경색

onHandleSprite/offHandleSprite : Sprite	켜짐/꺼짐 손잡이 스프라이트

handleOnPos/handleOffPos : Vector2	켜짐/꺼짐 손잡이 위치

앞에서 설명했던 BGM/효과음을 조절하는 탭이다 

BGM_Slider.cs, SFX_Slider.cs 두개를 통해 효과음과 브금 소리를 조절함

Start()

저장된 볼륨(BGM_Volume, 기본 0.2f) 로드 → 슬라이더 초기화 → SoundManager.Instance.bgmSource.volume 반영 → onValueChanged에 AdjustVolume 등록

AdjustVolume(float value)

전달된 볼륨을 SoundManager.Instance.bgmSource.volume에 즉시 반영, PlayerPrefs("BGM_Volume") 저장

2. 개인정보패널


3. 공지사항 패널

