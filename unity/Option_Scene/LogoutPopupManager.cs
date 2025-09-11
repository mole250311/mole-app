using UnityEngine;
using UnityEngine.SceneManagement;

public class LogoutPopupManager : MonoBehaviour
{
    public GameObject logoutPopupPanel;  // �˾� �г�
    public GameObject backgroundBlocker; // �˾� �ܺ� Ŭ�� ������ (Optional)

    // �˾� ����
    public void OpenPopup()
    {
        logoutPopupPanel.SetActive(true);
        if (backgroundBlocker != null)
            backgroundBlocker.SetActive(true);
        Time.timeScale = 0f; // ���� ���� (������)
    }

    // ���ư���
    public void ClosePopup()
    {
        logoutPopupPanel.SetActive(false);
        if (backgroundBlocker != null)
            backgroundBlocker.SetActive(false);
        Time.timeScale = 1f;
    }

    // �α׾ƿ� (�ٸ� ������ �̵�)
    public void Logout()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene("Login_Scene");  // �̵��� �� �̸��� ���⿡ �Է�
    }
}
