# Unity Mole 프로젝트
 이 저장소는 Unity로 만든 Mole 코드만 모아둔 것입니다.
 


 ## 프로젝트 소개 
 이 앱은 화학 구조를 직관적으로 탐색하고 학습할 수 있도록 만든 Unity 기반 교육용 앱.
 
 사용자는 3D 분자 모델, 퀴즈, 논문 검색, 튜툐리얼, 챗봇 기능들을 통해 학습을 진행할수 있음.
 
 ## 개발 기간
 2025-03-?? ~ ---
 ## 개발자소개
 김홍경 
 임소현
 이현우
 주성준
 조현우
 황예지
 최예인
 윤정우

 ## 개발환경
 Version: 6000.0.44fl1
 
 OS: Window
 
 visual studio code , visual studio, pycharm 
 
 Server: AWS EC2
 
 DataBase: ??
 
 아이디어 회의: Discord, Notion
 

 ## 아키텍쳐 
 그려주세요 

 ## 주요기능
⚫아미노산 탐색 

아미노산의 이름, 분류(극성/비극성 등), 구조 이미지를 DB에 저장한다.

Unity 내에서 아미노산 버튼을 누르면 해당 아미노산의 3D 분자 구조가 나타난다.

분자 구조는 360도 회전, 확대/축소, 즐겨찾기 기능과 함께 제공된다.


⚫퀴즈 시스템 

아미노산의 성질, 구조, 분류를 학습할 수 있는 퀴즈를 제공한다.

오답률과 유사 유형 문제를 분석하여 사용자의 약점을 피드백한다.

진행도와 즐겨찾기 데이터는 로컬/서버 DB에 저장되어 사용자별 맞춤 학습이 가능하다.

⚫논문 검색

PubMed API를 활용하여 관련 논문을 검색한다.

검색된 논문은 앱 내 카드 UI로 표시되며, 제목·초록을 번역하여 한국어로 제공한다.

최신순, 관련도순 정렬 및 즐겨찾기 기능 지원.

⚫챗봇

아미노산 학습 중 궁금한 점을 대화형으로 질문할 수 있는 챗봇을 제공한다.

기본 개념 설명부터 문제 풀이 보조, 논문 검색 안내까지 학습 도우미 역할을 수행한다.

⚫튜툐리얼

신규 사용자를 위해 단계별 오버레이 튜토리얼을 제공한다.

특정 버튼을 누르거나 모델을 조작해야 다음 단계로 넘어가는 행동 유도형 튜토리얼을 지원한다.

튜토리얼 완료 여부는 로컬에 저장되어 한 번만 실행된다.


## API
API 설명: ??


## 정우의 낙서 코드 

공통 부분 

1. 로딩화면
2. LoadingController.cs


         private string[] scenesToLoad = {"Loading_End_Scene", "Login_Scene", "Main_Simulation_Scene",
        "Thesis_Scene", "Favorite_Model_Scene", "Draw_Scene",
        "Search_3D", "Option_Scene", "Administrator_Scene"

    };


시작시 비동기 로드할 씬 이름 목록.

    void Start(){
    int refreshRate = Screen.currentResolution.refreshRate;

    Application.targetFrameRate = refreshRate;
    QualitySettings.vSyncCount = 0;
    StartCoroutine(LoadScenes());
    }



실행시 화면 주사율에 맞기 프레임을 고정

코루틴 LoadScnes()시작 ->씬들을 순차적으로 로드

로딩화면의 애니메이션

따로 .cs파일이 아닌 Animator Controller 방식임 

200장의 프레임을 스프라이트 애니메이션으로 묶음

Animator Controller는 유니티 자체 컴포넌트 



1. 오디오 (BGM/SFX)
   
2. SoundManageer.cs : 싱글톤 , 씬 전환에도 유지, 버튼 클릭 사운드 자동 바인딩
   
3. BGM/SFX Volume Slider: Player로 볼륨 저장/복원


        public class SoundManager : MonoBehaviour {
        public static SoundManager Instance;
        public AudioSource sfxSource;
        public AudioClip clickSound;
        public AudioSource bgmSource;
        public AudioClip bgmClip;
        private bool bgmStarted = false;

        private void Awake() {
            if (Instance != null && Instance != this) {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            // 씬 로드 시 버튼들에 클릭 사운드 자동 등록
            SceneManager.sceneLoaded += OnSceneLoaded;
        }
        private void OnSceneLoaded(Scene scene, LoadSceneMode mode) {
            if (!bgmStarted && scene.name == "Main_Simulation_Scene") {
                bgmSource.clip = bgmClip;
                bgmSource.loop = true;
                bgmSource.Play();
                bgmStarted = true;
            }
        // 모든 버튼에 클릭 사운드 추가
            foreach (var btn in FindObjectsOfType<Button>(true))
                btn.onClick.AddListener(PlayClickSound);
        }
        public void PlayClickSound() {
            if (clickSound != null && sfxSource != null)
                sfxSource.PlayOneShot(clickSound);
        }
     }


특징

DontDestroyOnLoad-> 씬 전환 시에도 음악 유지

모든 버튼 자동 탐색 -> 클릭 사운드 일괄 등록

BGM Slider.cs 

     float savedVolume = PlayerPrefs.GetFloat("BGM_Volume", 0.2f);
        slider.value = savedVolume;



 이전에 PlayerPrefs에서 이전의 저장된 BGM 볼륨 값을 불러옴 
 
 BGM_Volum 키로 저장된값이 없으면 0.2< 20퍼 를 사용함
 
 불러온 값을 슬라이더 초기값으로 설정 
 

    if (SoundManager.Instance?.bgmSource != null)
            SoundManager.Instance.bgmSource.volume = savedVolume;


 위에 매니저.cs 에 싱글톤이 존재하고 배경음이 유효하면 실제 배경음 적용

    slider.onValueChanged.AddListener(AdjustVolume); 

슬라이더가 움직일 때마다 AdjustVolume 함수 호출 되도록 등록 

SFX Silder.cs 파일도 거의 동일 이름만 달라짐 (효과음.)



1. 토글 슬라이더 UI (설정값 저장)
  
2. ToggleVisual.cs 파일 토글의 색상, 스프라이트 ,위치 변화를 제어하고 위에 PlayerPrefs로 상태저장<< 이게 아까 말했던 종료시키더라도 다시켰을때 저장된거 불러오는거


       public class ToggleVisual : MonoBehaviour {
            public Toggle toggle;
            public Image background;
            public RectTransform handle;
            public Image handleImage;
            public Color onColor = new Color(0.25f, 0.5f, 1f);
            public Color offColor = Color.gray;
            public Vector2 handleOnPos = new Vector2(10, 0);
            public Vector2 handleOffPos = new Vector2(-10, 0);
  
         void Start() {
            // 저장된 값 불러오기
            bool isOn = PlayerPrefs.GetInt("Toggle_Generic", 1) == 1;
            toggle.SetIsOnWithoutNotify(isOn);
            UpdateToggleUI(isOn);
            toggle.onValueChanged.AddListener(HandleChanged);
        }

        void HandleChanged(bool isOn) {
            UpdateToggleUI(isOn);
            PlayerPrefs.SetInt("Toggle_Generic", isOn ? 1 : 0);
            PlayerPrefs.Save();
        }
        void UpdateToggleUI(bool isOn) {
            background.color = isOn ? onColor : offColor;
            handle.anchoredPosition = isOn ? handleOnPos : handleOffPos;
        }
    }


특징

색상/스프라이트 동적변경

1. 튜토리얼 (단계별 안내 + 행동 대기)


2. TutorialManager.cs 에서 가져옴 Overlay 패널을 띄워 단계별로 설명 제공, 특정 단계는 사용자의 행동을 기다리다 진행
   
        public void Notify(string trigger) {
        if (!waitingForTrigger) return;

        if (step == 7 && trigger == "AminoAcidClicked") {
            step++;
            ShowStep();
            waitingForTrigger = false;
        }
    }

특징

위 코드는 스텝 7번째에 아미노산 클릭이라는 행동을 기다림

Notify 호출시 다음단계로 진행

튜툐리얼 완료 여부를 PlayerPrsfs에 기록하여 위에 음악처럼 저장되게 만들어 튜툐리얼은 최초1회만 시행

논문 부분

(검색어 입력-> 서버/papers호출-> 응답 JSON 파싱 -> 카드프리팹 인스턴스 생성/바인딩-> 패널전환)

PaperCardHandler.cs - 논문 검색 결과를 카드로 표시 클릭시 상세화면 표시 

    public void SetPaper(Paper p) {
        paper = p;
        var btn = GetComponent<Button>();
        btn.onClick.RemoveAllListeners();
        btn.onClick.AddListener(OnCardClicked);
    }

    public void OnCardClicked() {
        if (paper != null)
            PaperDetailUI.Instance.ShowPaperDetail(paper);
    }
특징

논문 데이터를 카드에 바인딩

클릭시 JSON 로그+ 상세화면 표시 

PubMed API검색 결과와 연동

PaperFetcher.cs 에서 가져옴 
1. 사용자 검색 -> API호출 ->파싱-> 맞는자리에 바인딩-> 뒤로가기 와 같은 걸 적용하는 파일 

         IEnumerator FetchPapers(string keyword, string order) {
         baseUrl = PlayerPrefs.GetString("ServerUrl"); // 서버 주소를 PlayerPrefs에서 가져옴
         string apiUrl = $"{baseUrl}/papers?query={EscapeURL(keyword)}&order={order}&limit=5&translate=true&lang=ko";

         var req = UnityWebRequest.Get(apiUrl);
         req.certificateHandler = new BypassCertificate(); // 테스트용 SSL 우회
         yield return req.SendWebRequest();

         if (req.result != Success) { // 실패 처리
           Debug.LogError("API 요청 실패: " + req.error);
           yield break;
         }

         // JSON → 객체화
         string json = req.downloadHandler.text;
         var response = JsonUtility.FromJson<PaperResponse>(json);
         // 서버가 results 또는 papers 중 무엇으로 주든 대응
         Paper[] list = (response.results != null && response.results.Length > 0)
                          ? response.results : response.papers;
         if (list == null || list.Length == 0) { /* 빈 결과 처리 */ yield break; }
         // 기존 카드 비우고
         foreach (Transform child in cardParent) Destroy(child.gameObject);
         // 새 카드 생성 & 바인딩
         foreach (var paper in list) {
           var card = Instantiate(cardPrefab, cardParent);
           // 카드 클릭 핸들러(상세 진입) 연결
           card.GetComponent<PaperCardHandler>()?.SetPaper(paper);
           // 내부 텍스트 참조
           var panel        = card.transform.Find("Panel");
           var titleText    = panel.Find("TitleText")?.GetComponent<TMP_Text>();
           var abstractText = panel.Find("AbstractText")?.GetComponent<TMP_Text>();
           var keywordsText = panel.Find("KeywordsText")?.GetComponent<TMP_Text>();
           var linkText     = panel.Find("LinkTextButton/LinkText")?.GetComponent<TMP_Text>();
           // 텍스트 세팅 (키워드 하이라이트 + 초록 100자 자르기)
           string title = HighlightKeyword(paper.title_ko, keyword);
           string abs   = HighlightKeyword(TruncateText(paper.abstract_ko, 100), keyword);
           titleText.text    = title;
           abstractText.text = abs;
           keywordsText.text = "";           // 
           linkText.text     = paper.link;   // 링크 표시
       }

요청 URL 구성: order(latest/relevance), limit=5, translate=true&lang=ko

SSL 임시 우회: BypassCertificate (배포 시 제거 권장)

응답 파싱: JsonUtility 사용

UI 생성: cardPrefab 복제 → 하위 Panel/TitleText... 경로로 TMP_Text 채우기

하이라이트/축약:

TruncateText(text, 100) → 최대 100자 + ...

HighlightKeyword(text, keyword, "#007BFF") → <color> 태그로 키워드 강조(대소문자 무시)



    public void OnBackToHome() {
      StopAllCoroutines();                      // 진행 중 네트워크 중단
      foreach (Transform child in cardParent)   // 카드 삭제
          Destroy(child.gameObject);

      Thesis_home?.SetActive(true);             // 홈 표시
      Thesis_main?.SetActive(false);            // 메인 숨김
      Thesis_main_detail?.SetActive(false);     // 디테일 숨김
    }
    public void HomeSearchBtn() {
      // 홈 → 메인 전환 + 기본 검색
      Thesis_home?.SetActive(false);
      Thesis_main?.SetActive(true);
      Thesis_main_detail?.SetActive(false);
      if (!string.IsNullOrEmpty(searchInputField.text))
          StartCoroutine(FetchPapers(searchInputField.text.Trim(), "relevance"));
    }

이 두개가 패널전환과 뒤로가기 

홈에서 검색 버튼을 누르면 메인 패널 활성화 후 관련도순 기본 검색 실행


 PaperDetailUI.cs

     public void ShowPaperDetail(Paper paper) {
        Debug.Log("📦 파싱된 Paper 객체: " + JsonUtility.ToJson(paper));

        // 리스트 패널 → 상세 패널 전환
        listPanel.SetActive(false);
        detailPanel.SetActive(true);

        // 제목 (한글 제목 우선)
        titleText.text = !string.IsNullOrEmpty(paper.title_ko) ? paper.title_ko : "(제목 없음)";
        titleEnglishText.text = paper.title_ko;

        // 유형
        typeText.text = paper.type != null && paper.type.Length > 0
            ? string.Join(", ", paper.type)
            : "유형 정보 없음";

        // 저자 (영문)
        authorsText.text = paper.authors_en != null && paper.authors_en.Length > 0
            ? string.Join(", ", paper.authors_en)
            : "저자 정보 없음";

        // 저널, 날짜, 페이지 (없으면 기본 문구)
        journalText.text = paper.journal != null && paper.journal.Length > 0 ? paper.journal : "저널 정보 없음";
        dateText.text    = paper.pub_date != null && paper.pub_date.Length > 0 ? paper.pub_date : "날짜 정보 없음";
        pageText.text    = paper.pages   != null && paper.pages.Length   > 0 ? paper.pages   : "페이지 정보 없음";

        // 초록 (한글 우선)
        abstractText.text = !string.IsNullOrEmpty(paper.abstract_ko)
            ? paper.abstract_ko
            : (!string.IsNullOrEmpty(paper.abstract_en) ? paper.abstract_en : "요약 없음");

        // 키워드 (현재 없음 → 전부 숨김 처리)
        keywordText1.text = "";
        keywordText2.text = "";
        keywordText3.text = "";
        keywordText1.transform.parent.gameObject.SetActive(false);
        keywordText2.transform.parent.gameObject.SetActive(false);
        keywordText3.transform.parent.gameObject.SetActive(false);
    }
논문 카드 클릭시 PaperCardHandler에서 ShowPaperDetail(Paper)호출(상세패널호출)

Paper 객체의 각필드를 UI에 반영

값이 없으면 정보 없음 표시 


뒤에 음 옵션패널쪽은 뭐 설명을해야하까 너무 기본적인거 코드로 박아놔서 뭐 적을게없네 

홍경이가 너무 잘해놔서 내가 할게없다 홍경이가 나빴어 ㅇㅇ 





