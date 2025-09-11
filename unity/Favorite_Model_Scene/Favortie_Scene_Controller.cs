using SQLite;        
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using TMPro;
using Unity.VisualScripting;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using static CreateTable;
using static UnityEngine.Rendering.DebugUI;

public class Favorite_Scene_Controller : MonoBehaviour
{
    public GameObject Favorite_Group_Prefab;
    public Transform Content;
    public GameObject FavoriteCount;
    public GameObject FavoriteScrollRect;
    public GameObject ProgressScrollRect;
    public TextMeshProUGUI Favorite_Count_Text;
    public Sprite Progress_0;
    public Sprite Progress_50;
    public Sprite Progress_100;
    public Sprite Progress_Blue_Btn;
    public Sprite Progress_Red_Btn;

    public ButtonGroupController buttonGroupController;

    public List<GameObject> prefabList = new List<GameObject>();

    //public Color buttonColor = Color.green;

    private SQLiteConnection db;
    //private SQLiteConnection quiz_db;

    private int quiz_count = 0;
    private int quiz_log_count = 0;
    void Start()
    {
        string dbPath = Path.Combine(Application.persistentDataPath, "myDB.db");
        db = new SQLiteConnection(dbPath);

        /*string quiz_dbPath = Path.Combine(Application.persistentDataPath, "quiz.db");
        quiz_db = new SQLiteConnection(quiz_dbPath);*/
        //LoadAminoAcidFavorites();
    }
    void OnEnable()
    {
        SceneManager.activeSceneChanged += OnActiveSceneChanged;
    }

    void OnDisable()
    {
        SceneManager.activeSceneChanged -= OnActiveSceneChanged;
    }

    void OnActiveSceneChanged(Scene oldScene, Scene newScene)
    {
        //Debug.Log($"[씬 전환] {oldScene.name} → {newScene.name}");

        LoadAminoAcidFavorites();
        LoadProgressData();
        SaveOpen();
        buttonGroupController.StartButtonState();
    }
    public void LoadAminoAcidFavorites()
    {
        // ✅ 0. 테이블 존재 여부 확인
        var tableExists = db.ExecuteScalar<int>(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='user_favorite';"
        );

        if (tableExists == 0)
        {
            Debug.LogWarning("user_favorite 테이블이 존재하지 않아 즐겨찾기를 불러올 수 없습니다.");
            return;
        }

        // ✅ 기존 콘텐츠 초기화
        foreach (Transform child in Content)
        {
            Destroy(child.gameObject);
        }

        // 1. 아미노산 챕터 page_id 가져오기
        var pages = db.Table<CreateTable.user_favorite>()
            .Select(f => f.chapter_id)
            .ToList();

        int totalPages = pages.Count;
        int groupCount = Mathf.CeilToInt(totalPages / 4f);
        int pageIndex = 0;

        /*        try
                {
                    quiz_count = quiz_db.Table<quiz>().Count();
                }
                catch (SQLiteException)
                {
                    // 테이블이 없으면 0으로 처리
                    quiz_count = 0;
                }

                try
                {
                    quiz_log_count = db.Table<quiz_log>().Count();
                }
                catch (SQLiteException)
                {
                    quiz_log_count = 0;
                }*/


        Favorite_Count_Text.text = "20/" + totalPages;
        /*Favorite_Count_Text.text = ((double)quiz_log_count / quiz_count * 100) +"%";*/

        for (int i = 0; i < groupCount; i++)
        {
            GameObject group = Instantiate(Favorite_Group_Prefab, Content);

            for (int j = 1; j <= 4; j++)
            {
                if (pageIndex >= totalPages)
                    break;

                string btnName = $"Favorite_Btn{j}";
                Transform btnTransform = group.transform.Find(btnName);

                if (btnTransform != null)
                {
                    UnityEngine.UI.Button btn = btnTransform.GetComponent<UnityEngine.UI.Button>();
                    if (btn != null)
                    {
                        TextMeshProUGUI tmpText = btn.GetComponentInChildren<TextMeshProUGUI>();
                        if (tmpText != null)
                            tmpText.text = pages[pageIndex];

                        foreach (var item in prefabList)
                        {
                            if (item.name == pages[pageIndex])
                            {
                                GameObject obj = Instantiate(item, btn.transform);
                                obj.transform.localPosition = new Vector3(0f, 0f, -20f);
                                obj.transform.localScale = new Vector3(5f, 5f, 5f);
                                obj.transform.SetAsLastSibling();
                            }
                        }

                        Image img = btn.GetComponent<Image>();
                        if (img != null)
                            img.color = new Color(1f, 1f, 1f, 1f);

                        Transform child = btn.transform.Find("Image");
                        if (child != null)
                        {
                            Image childImage = child.GetComponent<Image>();
                            childImage.color = new Color(1f, 1f, 1f, 1f);
                        }
                    }
                }

                pageIndex++;
            }
        }
    }

    public void SaveOpen()
    {
        FavoriteScrollRect.SetActive(true);
        FavoriteCount.SetActive(true);
        ProgressScrollRect.SetActive(false);
        QuizView.SetActive(false);
    }
    public void ProgressOpen()
    {
        var User = db.Table<users>()
                  .OrderBy(u => u.created_at)
                  .FirstOrDefault();

        FavoriteScrollRect.SetActive(false);
        FavoriteCount.SetActive(true);
        ProgressScrollRect.SetActive(true);
        QuizView.SetActive(false);
        Favorite_Count_Text.text = db.Table<OverallProgress>()
            .Where(f => f.user_id == User.user_id)
        .Select(f => f.total_progress_percent)
        .FirstOrDefault() + "%";
    }
    public GameObject QuizView;

    public void OpenQuizPanel()
    {
        QuizView.SetActive(true);
        FavoriteScrollRect.SetActive(false);
        FavoriteCount.SetActive(false);
        ProgressScrollRect.SetActive(false);
    }
    public GameObject PopupQuizPanel;  // 인스펙터에 연결

/*    public void OpenQuizPopup()
    {
        PopupQuizPanel.SetActive(true);
        Time.timeScale = 0; // UI 외부 인터랙션 막기
    }
    public Favorite_Scene_Controller controller;

    public void OnClick()
    {
        controller.OpenQuizPopup();
    }
*/

    /*public void CloseQuizPopup()
    {
        PopupQuizPanel.SetActive(false);
        Time.timeScale = 1;
    }*/
    public void LoadProgressData()
    {
        ProgressScrollRect.SetActive(true);
        string[] aminoAcids = {
            "Alanine", "Valine", "Leucine", "Isoleucine", "Proline",
            "Phenylalanine", "Tryptophan", "Methionine", "Glycine",
            "Serine", "Threonine", "Tyrosine", "Cysteine",
            "Glutamine", "Asparagine", "Asparticacid", "Glutamicacid",
            "Histidine", "Lysine", "Arginine"};
        foreach (string aa in aminoAcids)
        {
            string progressName = aa + "_Progress";
            string buttonName = aa + "_Progress_Btn";
            GameObject progressObj = GameObject.Find(progressName);
            GameObject btnObj = GameObject.Find(buttonName);
            Progress_Select_Btn psb = btnObj.GetComponent<Progress_Select_Btn>();

            //Image progressImg = progressObj.GetComponentInChildren<Image>();
            //Image progressFill = progressObj.transform.Find("ProgressFill").GetComponent<Image>();

            TextMeshProUGUI text = btnObj.GetComponentInChildren<TextMeshProUGUI>();
            Image btnImg = btnObj.GetComponentInChildren<Image>();

            var MoleQuestions = db.Table<quiz_log>()
                                 .Where(q => q.chapter == aa)
                                 .ToList();

            // 먼저 푼 문제 수가 전체 문제 수와 같은지 확인해야 함
            // 문제 수를 정해놓았다고 가정할 경우 예: 총 2문제
            int totalQuestionsInChapter = 8;

            if (MoleQuestions.Count == 0)
            {
                //progressImg.sprite = Progress_0;
                btnImg.sprite = Progress_Blue_Btn;
                text.text = "문제풀러가기";

                psb.quizNum = 1;
            }
            else if (MoleQuestions.Count < totalQuestionsInChapter)
            {
                //progressImg.sprite = Progress_50;
                btnImg.sprite = Progress_Blue_Btn;
                text.text = "이어하기";

                //var answeredNumbers = MoleQuestions.Select(q => q.question_number).ToList();
                var answeredNumbers = MoleQuestions
                .Select(q => {
                    int local = q.quiz_id % totalQuestionsInChapter;
                    return local == 0 ? totalQuestionsInChapter : local;
                })
                .ToList();
                var totalSet = Enumerable.Range(1, totalQuestionsInChapter);
                var notSolved = totalSet.Except(answeredNumbers);

                if (notSolved.Any())
                {
                    int minUnsolved = notSolved.Min();

                    psb.quizNum = minUnsolved;
                    //Debug.Log($"{aa}: 아직 안 푼 가장 낮은 문제 번호는 {minUnsolved}");
                }

            }
            else if (MoleQuestions.Count == totalQuestionsInChapter)
            {
                bool hasWrong = MoleQuestions.Any(q => q.status == "wrong");
                bool allCorrect = MoleQuestions.All(q => q.status == "correct");

                if (hasWrong)
                {
                    //progressImg.sprite = Progress_100;
                    btnImg.sprite = Progress_Red_Btn;
                    text.text = "오답 확인하러가기";

                    // ✅ 여기서 가장 낮은 틀린 문제 번호 출력
                    /*var wrongMin = MoleQuestions
                        .Where(q => q.status == "wrong")
                        .Min(q => q.question_number);*/

                    var wrongMin = MoleQuestions
                    .Where(q => q.status == "wrong")
                    .Select(q => {
                        int local = q.quiz_id % totalQuestionsInChapter;
                        return local == 0 ? totalQuestionsInChapter : local;
                    })
                    .Min();

                    psb.quizNum = wrongMin;

                    //Debug.Log($"{aa}: 가장 먼저 틀린 문제 번호 = {wrongMin}");
                }
                else if (allCorrect)
                {
                    btnImg.sprite = Progress_Blue_Btn;
                    text.text = "완료";

                    psb.quizNum = 1;
                }
            }
            Slider slider = progressObj.GetComponentInChildren<Slider>();
            if (slider != null)
            {
                slider.minValue = 0f;
                slider.maxValue = 1f;
                slider.value = MoleQuestions.Count / (float)totalQuestionsInChapter;
            }
        }
        ProgressScrollRect.SetActive(false);
    }

    public class NamedPrefab
    {
        public string name;       // 프리팹 이름 (키값)
        public GameObject prefab; // 실제 프리팹
    }
}
