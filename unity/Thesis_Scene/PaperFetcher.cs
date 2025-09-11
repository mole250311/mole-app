using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using TMPro;
using UnityEngine.UI;
using System.Text.RegularExpressions;

[System.Serializable]
public class Paper
{
    public string pmid;
    public string title_en;
    public string title_ko;
    public string abstract_en;
    public string abstract_ko;
    public string[] authors_en;
    public string[] authors_ko;
    public string type;
    public string journal;
    public string pub_date;   // 옛 필드명
    public string published;  // 새 필드명 대응
    public string pages;
    public string link;
}

[System.Serializable]
public class PaperResponse
{
    public string query;
    public string order;
    public int limit;
    public bool translate;

    public Paper[] papers;   // 서버에서 papers로 내려올 때
    public Paper[] results;  // 서버에서 results로 내려올 때
}

public class PaperFetcher : MonoBehaviour
{
    /*[Header("뒤로가기 버튼")]
    public Button backButton;*/

    [Header("입력 필드 및 버튼")]
    public TMP_InputField searchInputField;
    /*public Button searchButton;
    public Button searchLatestButton;
    public Button searchRelevanceButton;*/

    [Header("패널 오브젝트")]
    public GameObject Thesis_home;
    public GameObject Thesis_main;
    public GameObject Thesis_main_detail;

    [Header("카드 UI")]
    public GameObject cardPrefab;
    public Transform cardParent;

    /*private string baseUrl = "https://15.165.159.228:8000";*/
    //private string baseUrl = PlayerPrefs.GetString("ServerUrl");
    private string baseUrl;

    void Start()
    {
        //searchButton.onClick.AddListener(OnSearchDefault);
        //searchLatestButton.onClick.AddListener(OnSearchLatest);
        //searchRelevanceButton.onClick.AddListener(OnSearchRelevance);

        //if (backButton != null) backButton.onClick.AddListener(OnBackToHome);
    }
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            // 메인이 열려있을 때만 홈으로
            if (Thesis_main != null && Thesis_main.activeSelf)
                OnBackToHome();
        }
    }



    /// <summary>
    /// 기본 검색 (관련도순)
    /// </summary>
    public void OnSearchDefault()
    {
        string keyword = searchInputField.text.Trim();
        Debug.Log("🔍 기본 검색(관련도) keyword=" + keyword);
        if (!string.IsNullOrEmpty(keyword))
            StartCoroutine(FetchPapers(keyword, "relevance"));
    }
    public void OnBackToHome()
    {
        // 코루틴/요청 중이면 정리
        StopAllCoroutines();

        // 카드들 정리
        if (cardParent != null)
        {
            foreach (Transform child in cardParent)
                Destroy(child.gameObject);
        }

        // 입력 초기화(원하면 주석 해제)
        // if (searchInputField != null) searchInputField.text = "";

        // 패널 전환
        if (Thesis_home != null) Thesis_home.SetActive(true);
        if (Thesis_main != null) Thesis_main.SetActive(false);
        if (Thesis_main_detail != null) Thesis_main_detail.SetActive(false);

        Debug.Log("⬅️ 뒤로가기: 메인/디테일 → 홈");
    }


    /// <summary>
    /// 최신순 검색
    /// </summary>
    public void OnSearchLatest()
    {
        string keyword = searchInputField.text.Trim();
        Debug.Log("🔍 최신순 검색 keyword=" + keyword);
        if (!string.IsNullOrEmpty(keyword))
            StartCoroutine(FetchPapers(keyword, "latest"));
    }

    /// <summary>
    /// 관련도순 검색
    /// </summary>
    public void OnSearchRelevance()
    {
        string keyword = searchInputField.text.Trim();
        Debug.Log("🔍 관련도순 검색 keyword=" + keyword);
        if (!string.IsNullOrEmpty(keyword))
            StartCoroutine(FetchPapers(keyword, "relevance"));
    }
    IEnumerator FetchPapers(string keyword, string order)
    {
        baseUrl = PlayerPrefs.GetString("ServerUrl");

        string apiUrl = $"{baseUrl}/papers?query={UnityWebRequest.EscapeURL(keyword)}&order={order}&limit=5&translate=true&lang=ko";
        Debug.Log("📡 요청 URL: " + apiUrl);

        UnityWebRequest request = UnityWebRequest.Get(apiUrl);
        request.certificateHandler = new BypassCertificate();

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("❌ API 요청 실패: " + request.error);
            yield break;
        }

        string json = request.downloadHandler.text;
        Debug.Log("📦 응답 JSON: " + json);

        PaperResponse response = JsonUtility.FromJson<PaperResponse>(json);

        // papers/results 둘 다 체크
        Paper[] list = (response.results != null && response.results.Length > 0)
            ? response.results
            : response.papers;

        if (list == null || list.Length == 0)
        {
            Debug.LogWarning("⚠️ 서버에서 논문 리스트가 비었습니다. (results/papers 없음)");
            yield break;
        }

        Debug.Log("📄 논문 수: " + list.Length);

        // 기존 카드 삭제
        foreach (Transform child in cardParent)
        {
            Destroy(child.gameObject);
        }

        // 새 카드 생성
        foreach (Paper paper in list)
        {
            GameObject card = Instantiate(cardPrefab, cardParent);

            PaperCardHandler handler = card.GetComponent<PaperCardHandler>();
            if (handler != null)
            {
                handler.SetPaper(paper); // 필요한 경우에만
            }

            Transform panel = card.transform.Find("Panel");
            if (panel == null)
            {
                Debug.LogError("❌ Panel 오브젝트 없음");
                continue;
            }

            var titleText = panel.Find("TitleText")?.GetComponent<TMP_Text>();
            var abstractText = panel.Find("AbstractText")?.GetComponent<TMP_Text>();
            var keywordsText = panel.Find("KeywordsText")?.GetComponent<TMP_Text>();
            var linkText = panel.Find("LinkTextButton/LinkText")?.GetComponent<TMP_Text>();


            if (titleText == null || abstractText == null || keywordsText == null || linkText == null)
            {
                Debug.LogError("❌ 카드 내부 텍스트 연결 실패");
                continue;
            }

            string keywordColored = HighlightKeyword(paper.title_ko, keyword);
            string abstractTruncated = TruncateText(paper.abstract_ko, 100);
            string abstractColored = HighlightKeyword(abstractTruncated, keyword);

            titleText.text = keywordColored;
            abstractText.text = abstractColored;
            keywordsText.text = "";  // 서버에 keywords 없음
            linkText.text = paper.link;

        }
    }

    /*IEnumerator FetchPapers(string keyword)
    {
        baseUrl = PlayerPrefs.GetString("ServerUrl");
        //Debug.Log("🌐 ServerUrl: " + PlayerPrefs.GetString("ServerUrl"));

        //string apiUrl = "https://15.165.159.228:8000" + "/papers?query=" + UnityWebRequest.EscapeURL(keyword);
        string apiUrl = baseUrl + "/papers?query=" + UnityWebRequest.EscapeURL(keyword);
        Debug.Log("📡 요청 URL: " + apiUrl);

        UnityWebRequest request = UnityWebRequest.Get(apiUrl);
        request.certificateHandler = new BypassCertificate(); // SSL 우회 (테스트용)

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("❌ API 요청 실패: " + request.error);
            yield break;
        }

        string json = request.downloadHandler.text;
        Debug.Log("📦 응답 JSON: " + json);

        PaperResponse response = JsonUtility.FromJson<PaperResponse>(json);
        Debug.Log("📄 논문 수: " + response.papers.Length);

        // 기존 카드 삭제
        foreach (Transform child in cardParent)
        {
            Destroy(child.gameObject);
        }

        // 새 카드 생성
        foreach (Paper paper in response.papers)
        {
            GameObject card = Instantiate(cardPrefab, cardParent);

            PaperCardHandler handler = card.GetComponent<PaperCardHandler>();
            if (handler != null)
            {
                handler.SetPaper(paper); // 필요한 경우에만
            }

            Transform panel = card.transform.Find("Panel");
            if (panel == null)
            {
                Debug.LogError("❌ Panel 오브젝트 없음");
                continue;
            }

            var titleText = panel.Find("TitleText")?.GetComponent<TMP_Text>();
            var abstractText = panel.Find("AbstractText")?.GetComponent<TMP_Text>();
            var keywordsText = panel.Find("KeywordsText")?.GetComponent<TMP_Text>();
            var linkText = panel.Find("LinkTextButton/LinkText")?.GetComponent<TMP_Text>();


            if (titleText == null || abstractText == null || keywordsText == null || linkText == null)
            {
                Debug.LogError("❌ 카드 내부 텍스트 연결 실패");
                continue;
            }

            string keywordColored = HighlightKeyword(paper.title_ko, keyword);
            string abstractTruncated = TruncateText(paper.abstract_ko, 100);
            string abstractColored = HighlightKeyword(abstractTruncated, keyword);

            titleText.text = keywordColored;
            abstractText.text = abstractColored;
            keywordsText.text = "";  // 서버에 keywords 없음
            linkText.text = paper.link;

        }
    }*/

    private string TruncateText(string text, int maxLength)
    {
        if (string.IsNullOrEmpty(text)) return "";
        return text.Length <= maxLength ? text : text.Substring(0, maxLength) + "...";
    }

    private string HighlightKeyword(string text, string keyword, string colorHex = "#007BFF")
    {
        if (string.IsNullOrEmpty(text) || string.IsNullOrEmpty(keyword)) return text;
        return Regex.Replace(text, Regex.Escape(keyword), $"<color={colorHex}>{keyword}</color>", RegexOptions.IgnoreCase);
    }

    public void HomeSearchBtn()
    {
        if (Thesis_home != null) Thesis_home.SetActive(false);
        if (Thesis_main != null) Thesis_main.SetActive(true);
        if (Thesis_main_detail != null) Thesis_main_detail.SetActive(false);

        string keyword = searchInputField.text.Trim();
        Debug.Log("🔍 기본 검색(관련도) keyword=" + keyword);
        if (!string.IsNullOrEmpty(keyword))
            StartCoroutine(FetchPapers(keyword, "relevance"));

        Debug.Log("🧭 HomeSearchBtn(): 홈 → 메인 패널로 전환됨");
    }

    class BypassCertificate : CertificateHandler
    {
        protected override bool ValidateCertificate(byte[] certificateData)
        {
            return true; // SSL 우회 (테스트 서버용)
        }
    }
}
