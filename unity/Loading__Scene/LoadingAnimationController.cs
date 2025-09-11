using UnityEngine;
using UnityEngine.SceneManagement;

public class LoadingAnimationController : MonoBehaviour
{
    public string nextSceneName = "SampleScene"; // ��ȯ�� �� �̸�
    public float animationSpeed = 3f; // �ִϸ��̼� �ӵ� (���ϴ� ���)

    private Animator animator;

    void Start()
    {
        animator = GetComponent<Animator>();
        animator.speed = animationSpeed;

        // �ִϸ��̼� �� ���� ��������
        float animationLength = animator.runtimeAnimatorController.animationClips[0].length / animationSpeed;

        // �ִϸ��̼� ������ ���� ������ �Ѿ�� (Invoke ���)
        Invoke("LoadNextScene", animationLength);
    }

    void LoadNextScene()
    {
        SceneManager.LoadScene(nextSceneName);
    }
}
