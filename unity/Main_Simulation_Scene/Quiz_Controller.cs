using SQLite;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using static CreateTable;
using static Quiz_Controller;

public class Quiz_Controller : MonoBehaviour
{
    public MainBtnController MBC;

    public GameObject MultipleChoiceQuiz;
    //public GameObject WordQuiz;
    public GameObject AnswerUI;

    private int QuizAnswerNum;
    public TextMeshProUGUI QuizText1;
    public Button QuizAnswerBtn1_1;
    public Button QuizAnswerBtn1_2;
    public Button QuizAnswerBtn1_3;
    public Button QuizAnswerBtn1_4;

    public TextMeshProUGUI Quiz_Answer_Text;
    private string[] Quiz_Answer_List;
    public Image AnswerImage;
    public Sprite AnswerImage_O; 
    public Sprite AnswerImage_X;

    private SQLiteConnection db;
    private SQLiteConnection quiz_db;

    private string Quiz_chapter;
    //private int Quiz_questionNumber;
    private string Quiz_status;

    private int quiz_id_save;

    private int quiz_solved = 0;

    private DateTime startTime;
    private DateTime endTime;

    private Dictionary<string, List<QuizData>> quizCache = new Dictionary<string, List<QuizData>>();

    //private string serverUrl = PlayerPrefs.GetString("ServerUrl");
    private string serverUrl;

    void Start()
    {
        string dbPath = Path.Combine(Application.persistentDataPath, "myDB.db");
        db = new SQLiteConnection(dbPath);

        string quiz_dbPath = Path.Combine(Application.persistentDataPath, "quiz.db");
        quiz_db = new SQLiteConnection(quiz_dbPath);
    }

    public void MultipleChoiceQuizOpen(int n)
    {
        CloseUI();
        MultipleChoiceQuiz.SetActive(true);
        SetQuiz(n);
        Quiz_chapter = MBC.NowModelName;
        //Quiz_questionNumber = n;
        //StartCoroutine(GetQuizInfo(1));
    }

    /*public void AnswerChoice(int n)
    {
        CloseUI();
        AnswerUI.SetActive(true);
        if (QuizAnswerNum == n)
        {
            AnswerImage.sprite = AnswerImage_O;
            Quiz_Answer_Text.text = Quiz_Answer_List[n-1];
            Quiz_status = "correct";
        }
        else
        {
            AnswerImage.sprite = AnswerImage_X;
            Quiz_Answer_Text.text = Quiz_Answer_List[n-1];
            Quiz_status = "wrong";
        }
        SaveQuizStatus();
    }*/

    public void AnswerChoice(int n)
    {
        CloseUI();
        AnswerUI.SetActive(true);

        if (QuizAnswerNum == n)
        {
            AnswerImage.sprite = AnswerImage_O;
            Quiz_Answer_Text.text = "정답입니다!";
            Quiz_status = "correct";
        }
        else
        {
            AnswerImage.sprite = AnswerImage_X;
            Quiz_Answer_Text.text = "오답입니다.";
            Quiz_status = "wrong";
        }
        endTime = DateTime.Now;

        SaveQuizStatus();
    }

    void SetQuiz(int quizIndex)
    {
        startTime = DateTime.Now;

        string currentAmino = MBC.NowModelName;

        if (PlayerPrefs.GetInt("Login_State") == 0)
        {
            if(quiz_solved == 0)
            {
                quiz_solved = quiz_db.Table<quiz>().Count();
            }
            OfflineLoadQuiz(currentAmino, quizIndex);
        }
        else if (PlayerPrefs.GetInt("Login_State") == 1)
        {
            if (quizCache.ContainsKey(currentAmino))
            {
                Debug.Log($"🧠 캐시 사용: {currentAmino}");
                LoadQuizFromCache(currentAmino, quizIndex);
            }
            else
            {
                Debug.Log($"🌐 서버 요청: {currentAmino}");
                StartCoroutine(OnlineLoadQuiz(currentAmino, quizIndex));
            }
        }
    }

    void LoadQuizFromCache(string aminoAcid, int quizIndex)
    {
        List<QuizData> quizzes = quizCache[aminoAcid];

        if (quizIndex - 1 >= quizzes.Count)
        {
            Debug.LogWarning("⚠️ 캐시된 퀴즈 중 해당 인덱스 없음");
            return;
        }

        QuizData selected = quizzes[quizIndex - 1];
        QuizText1.text = "Q : " + selected.question;

        List<string> options = ParseOptions(selected.options);
        if (options.Count < 4)
        {
            Debug.LogWarning("⚠️ 옵션 수가 4개 미만입니다.");
            return;
        }

        SetOptionText(QuizAnswerBtn1_1, "A", options[0]);
        SetOptionText(QuizAnswerBtn1_2, "B", options[1]);
        SetOptionText(QuizAnswerBtn1_3, "C", options[2]);
        SetOptionText(QuizAnswerBtn1_4, "D", options[3]);

        QuizAnswerNum = GetAnswerIndex(options, selected.answer);
        //Debug.Log("✅ 캐시에서 로드된 정답 인덱스: " + QuizAnswerNum);
    }


    void OfflineLoadQuiz(string aminoAcid, int quizIndex)
    {
        var quizList = quiz_db.Table<quiz>()
                         .Where(q => q.amino_acid == aminoAcid)
                         .ToList();

        if (quizIndex - 1 >= quizList.Count) return;

        var quiz_data = quizList[quizIndex - 1];
        QuizText1.text = $"Q : {quiz_data.question}";

        quiz_id_save = quiz_data.quiz_id;

        List<string> options = ParseOptions(quiz_data.options);

        QuizAnswerBtn1_1.GetComponentInChildren<TextMeshProUGUI>().text = "A : " + options[0];
        QuizAnswerBtn1_2.GetComponentInChildren<TextMeshProUGUI>().text = "B : " + options[1];
        QuizAnswerBtn1_3.GetComponentInChildren<TextMeshProUGUI>().text = "C : " + options[2];
        QuizAnswerBtn1_4.GetComponentInChildren<TextMeshProUGUI>().text = "D : " + options[3];

        QuizAnswerNum = GetAnswerIndex(options, quiz_data.answer);
    }

    IEnumerator OnlineLoadQuiz(string aminoAcid, int quizIndex)
    {
        serverUrl = PlayerPrefs.GetString("ServerUrl");
        string url = serverUrl+$"/quizzes?amino_acid={UnityWebRequest.EscapeURL(aminoAcid)}";

        UnityWebRequest www = UnityWebRequest.Get(url);
        www.certificateHandler = new BypassCertificate(); // 인증서 무시 (테스트 서버에서만 사용)

        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("❌ 퀴즈 불러오기 실패: " + www.error);
            yield break;
        }

        string json = www.downloadHandler.text;
        Debug.Log("✅ 응답 JSON: " + json);

        QuizListWrapper wrapper = JsonUtility.FromJson<QuizListWrapper>(FixJson(json));

        List<QuizData> quizzes = wrapper.quizzes;
        quizCache[aminoAcid] = quizzes; // 캐시에 저장

        if (quizIndex - 1 >= quizzes.Count)
        {
            Debug.LogWarning("⚠️ 해당 인덱스의 퀴즈가 존재하지 않습니다.");
            yield break;
        }

        QuizData selected = quizzes[quizIndex - 1];

        QuizText1.text = "Q : " + selected.question;

        List<string> options = ParseOptions(selected.options);

        if (options.Count < 4)
        {
            Debug.LogWarning("⚠️ 옵션 수가 4개 미만입니다.");
            yield break;
        }

        SetOptionText(QuizAnswerBtn1_1, "A", options[0]);
        SetOptionText(QuizAnswerBtn1_2, "B", options[1]);
        SetOptionText(QuizAnswerBtn1_3, "C", options[2]);
        SetOptionText(QuizAnswerBtn1_4, "D", options[3]);

        QuizAnswerNum = GetAnswerIndex(options, selected.answer);
        //Debug.Log("✅ 정답 인덱스: " + QuizAnswerNum);
    }
    private string FixJson(string json)
    {
        // 배열로 시작하면 강제로 감쌈
        if (json.TrimStart().StartsWith("["))
        {
            return "{\"quizzes\":" + json + "}";
        }
        return json;
    }

    void SetOptionText(Button button, string label, string content)
    {
        var textComp = button.GetComponentInChildren<TextMeshProUGUI>();
        if (textComp != null)
        {
            textComp.text = $"{label} : {content}";
        }
        else
        {
            Debug.LogError($"❌ {label} 버튼에 TextMeshProUGUI가 없음");
        }
    }

    /*IEnumerator GetQuizInfo(int quizId)
    {
        Debug.Log("실행");


        string url = $"https://15.165.159.228:8000/quizzes/{quizId}";

        UnityWebRequest request = UnityWebRequest.Get(url);
        request.certificateHandler = new BypassCertificate(); 

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("❌ 요청 실패: " + request.error);
        }
        else
        {
            string json = request.downloadHandler.text;
            Debug.Log("✅ 퀴즈 응답:\n" + json);

            // 파싱 예시
            QuizWrapper quizWrapper = JsonUtility.FromJson<QuizWrapper>(json);
            Debug.Log("🔍 문제: " + quizWrapper.quiz.question);
            Debug.Log("🔍 정답: " + quizWrapper.quiz.answer);
            Debug.Log("🔍 옵션: " + quizWrapper.quiz.options);
        }
    }*/

    List<string> ParseOptions(string raw)
    {
        string cleaned = raw.Replace("[", "").Replace("]", "").Replace("'", "").Replace("\"", "");
        return new List<string>(cleaned.Split(','));
    }

    int GetAnswerIndex(List<string> options, string answer)
    {
        for (int i = 0; i < options.Count; i++)
        {
            if (options[i].Trim() == answer.Trim())
                return i + 1;  // 버튼 번호는 1부터 시작
        }
        return -1;
    }

    void CloseUI()
    {
        MultipleChoiceQuiz.SetActive(false);
        AnswerUI.SetActive(false);
    }

/*    public void SelectQuizStatus()
    {
        Quiz_chapter = MBC.NowModelName;
        Quiz_questionNumber = Quiz_num;
    }*/

    public void SaveQuizStatus()
    {
        /*var existing = db.Table<quiz_log>().Where(q => q.chapter == Quiz_chapter && q.question_number == Quiz_questionNumber).FirstOrDefault();*/
        var existing = db.Table<quiz_log>().Where(q => q.chapter == Quiz_chapter && q.quiz_id == quiz_id_save).FirstOrDefault();
        var User = db.Table<users>()
                  .OrderBy(u => u.created_at)
                  .FirstOrDefault();

        if (existing != null)
        {
            existing.status = Quiz_status;
            existing.answered_at = (endTime - startTime).TotalSeconds;
            db.Update(existing);
        }
        else
        {
            db.Insert(new quiz_log
            {
                user_id = User.user_id,
                quiz_id = quiz_id_save,
                chapter = Quiz_chapter,
                //question_number = Quiz_questionNumber,
                status = Quiz_status,
                answered_at = (endTime - startTime).TotalSeconds
            });
            db.Delete<OverallProgress>(User.user_id);
            db.Insert(new OverallProgress
            {
                user_id = User.user_id,
                total_solved = quiz_solved,
                total_progress_percent = ((double)db.Table<quiz_log>().Count() / quiz_solved * 100)
            });
        }
    }

    [System.Serializable]
    public class QuizData
    {
        public int id;
        public string amino_acid;
        public string question;
        public string answer;
        public string options;
        public string grade;
        public string created_at;
        public string topic;
    }

    [System.Serializable]
    public class QuizListWrapper
    {
        public List<QuizData> quizzes;
    }

    public static class JsonHelper
    {
        public static List<T> FromJson<T>(string json)
        {
            string newJson = "{\"Items\":" + json + "}";
            Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(newJson);
            return wrapper.Items;
        }

        [System.Serializable]
        private class Wrapper<T>
        {
            public List<T> Items;
        }
    }

    class BypassCertificate : CertificateHandler
    {
        protected override bool ValidateCertificate(byte[] certificateData)
        {
            return true; // 인증서 무시하고 통과시킴
        }
    }
}