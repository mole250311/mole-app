using System;
using System.Collections;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using static System.Net.Mime.MediaTypeNames;
using static UnityEngine.Rendering.DebugUI;

public class UserRegister : MonoBehaviour
{

    public GameObject FindAccountUIManagerObj;
    FindAccountUIManager find_account_uI_manage;

    /*public string serverUrl = "https://15.164.210.13:8000/users";*/
    //private string serverUrl = PlayerPrefs.GetString("ServerUrl");
    public TMP_InputField IDInputField;
    public TMP_InputField PWInputField;
    public TMP_InputField EmailInputField;
    public TMP_InputField NicknameInputField;
    public TMP_InputField Num1InputField;
    public TMP_InputField Num2InputField;
    public TMP_InputField Num3InputField;
    public TMP_Dropdown Year;
    public TMP_Dropdown Month;
    public TMP_Dropdown Day;
    public TMP_InputField Department;
    public TMP_Dropdown Grade;

    private string serverUrl;


    public void OnRegisterTest()
    {
        Debug.Log("입력된 IDInputField: " + IDInputField.text);
        Debug.Log("입력된 PWInputField: " + PWInputField.text);
        Debug.Log("입력된 EmailInputField: " + EmailInputField.text);
        Debug.Log("입력된 NicknameInputField: " + NicknameInputField.text);
        Debug.Log("입력된 전화: " + Num1InputField.text+"-"+Num2InputField.text+"-"+Num3InputField.text);
        Debug.Log("입력된 날짜: " + Year.options[Year.value].text+"년"+ Month.options[Month.value].text+"월"+ Day.options[Day.value].text+"일");
        Debug.Log("입력된 Department: " + Department.text);
        Debug.Log("입력된 Grade: " + Grade.options[Grade.value].text);
    }


    public void OnRegisterButtonClicked()
    {
        StartCoroutine(SendUserData());
    }

    public void OnDeleteUserButtonClicked(string userId)
    {
        StartCoroutine(DeleteUser(userId));
    }

    /*public void OnGetUserInfoButtonClicked(string userId)
    {
        StartCoroutine(GetUserInfo(userId));
    }*/

    public void OnGetUserIDButtonClicked()
    {
        StartCoroutine(GetUserIdByEmail());
    }

    IEnumerator SendUserData()
    {
        // 서버에서 salt를 생성하므로 클라이언트에서는 평문 비밀번호만 전송
        User user = new User
        {
            user_id = IDInputField.text,
            username = NicknameInputField.text,
            password = PWInputField.text,  // 평문 그대로 전송
            email = EmailInputField.text,
            birth_date =  Year.options[Year.value].text + "-" 
            + Month.options[Month.value].text + "-" 
            + Day.options[Day.value].text

        };

        string json = JsonUtility.ToJson(user);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

        serverUrl = PlayerPrefs.GetString("ServerUrl");

        using (UnityWebRequest request = UnityWebRequest.Put(serverUrl+ "/users/register", bodyRaw))
        {
            request.method = UnityWebRequest.kHttpVerbPOST;
            request.SetRequestHeader("Content-Type", "application/json");
            request.certificateHandler = new BypassCertificate();

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"❌ 등록 실패: {request.error}");
                ServerResponse response = JsonUtility.FromJson<ServerResponse>(request.downloadHandler.text);
                Debug.LogError(response.message);
            }
            else
            {
                Debug.Log("✅ 유저 등록 성공");
                ServerResponse response = JsonUtility.FromJson<ServerResponse>(request.downloadHandler.text);
                Debug.Log(response.message); // 서버 응답 확인
            }
        }
    }

    IEnumerator DeleteUser(string userId)
    {
        // JSON 생성
        DeleteRequest deleteReq = new DeleteRequest { user_id = userId };
        string json = JsonUtility.ToJson(deleteReq);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

        serverUrl = PlayerPrefs.GetString("ServerUrl");

        using (UnityWebRequest request = UnityWebRequest.Put(serverUrl+ "/users/delete", bodyRaw))
        {
            request.method = UnityWebRequest.kHttpVerbPOST;
            request.SetRequestHeader("Content-Type", "application/json");
            request.certificateHandler = new BypassCertificate();

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"❌ 회원 삭제 실패: {request.error}");
                Debug.LogError(request.downloadHandler.text);
            }
            else
            {
                ServerResponse response = JsonUtility.FromJson<ServerResponse>(request.downloadHandler.text);
                Debug.Log($"✅ 회원 삭제 성공: {response.message}");
            }
        }
    }

    IEnumerator GetUserInfo(string userId)
    {
        serverUrl = PlayerPrefs.GetString("ServerUrl");

        string url = serverUrl+$"/users/info?user_id={userId}";

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.certificateHandler = new BypassCertificate();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            string json = request.downloadHandler.text;
            Debug.Log($"[서버 응답] {json}");

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"❌ 유저 정보 조회 실패: {request.error}");
            }
            else
            {
                try
                {
                    UserWrapper wrapper = JsonUtility.FromJson<UserWrapper>(json);
                    UserInfo user = wrapper.user;

                    Debug.Log($"✅ 유저 정보\nID: {user.user_id}\n이름: {user.username}\n이메일: {user.email}\n생일: {user.birth_date}");
                }
                catch
                {
                    Debug.LogError("⚠️ JSON 파싱 실패");
                }
            }
        }
    }
    IEnumerator GetUserIdByEmail()
    {
        serverUrl = PlayerPrefs.GetString("ServerUrl");

        string url = $"{serverUrl}/users/info-by-email?email={UnityWebRequest.EscapeURL(find_account_uI_manage.emailIDInput.text)}";
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.certificateHandler = new BypassCertificate();
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Accept", "application/json");

            yield return request.SendWebRequest();

            string json = request.downloadHandler.text;
            Debug.Log($"[서버 응답] {json}");

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"❌ 유저 ID 조회 실패: {request.error}");
                yield break;
            }

            try
            {
                UserWrapper wrapper = JsonUtility.FromJson<UserWrapper>(json);
                if (wrapper == null || wrapper.user == null)
                {
                    Debug.LogError("⚠️ JSON 파싱 실패 또는 user 필드 없음");
                    yield break;
                }

                UserInfo user = wrapper.user;
                Debug.Log($"✅ 조회 성공: 이메일 {user.email} → ID {user.user_id}");

                // ID 찾기 UI에 ID를 넘겨주는 쪽이 자연스러워 보여서 이렇게 변경
                find_account_uI_manage.OnClickFindID(user.user_id, DateTime.Today.ToString("yyyy-MM-dd"));
            }
            catch (Exception e)
            {
                Debug.LogError($"⚠️ JSON 파싱 예외: {e.Message}");
            }
        }
    }

    class BypassCertificate : CertificateHandler
    {
        protected override bool ValidateCertificate(byte[] certificateData)
        {
            return true; // 인증서 무시하고 통과시킴 (주의: 운영 환경에선 제거)
        }
    }

    [System.Serializable]
    public class User
    {
        public string user_id;
        public string username;
        public string password;
        public string email;
        public string birth_date;
    }

    [System.Serializable]
    public class ServerResponse
    {
        public string message;
    }

    [System.Serializable]
    public class DeleteRequest
    {
        public string user_id;
    }

    [System.Serializable]
    public class UserWrapper
    {
        public UserInfo user;
    }

    [System.Serializable]
    public class UserInfo
    {
        public string user_id;
        public string username;
        public string email;
        public string birth_date;
    }
}
