using UnityEngine;
using UnityEngine.UI;

public class ArrowToggle : MonoBehaviour
{
    [Header("Ŭ�� Ʈ����(�� ��ư)")]
    public Button trigger;

    [Header("��ĥ ���� �г�")]
    public GameObject content;

    [Header("ȭ��ǥ �̹���")]
    public Image arrow;

    [Header("��������Ʈ ��ü(����)")]
    public Sprite collapsedSprite;     // ����
    public Sprite expandedSprite;      // ����

    [Header("ȸ��(Z��, ��)")]
    public float collapsedZ = 0f;
    public float expandedZ = 270f;

    [Header("�ʱ� ����")]
    public bool startOpen = false;

    [HideInInspector] public bool controlledByGroup = false; // �׷��� ���� ������
    private bool isOpen;

    void Awake()
    {
        // �׷��� �������� ���� ���� �ڱ� ������ Ŭ�� ���ε�
        if (!controlledByGroup && trigger)
            trigger.onClick.AddListener(Toggle);
    }

    void OnEnable() => Set(startOpen, true);

    public void Toggle() => Set(!isOpen);

    public void ForceSet(bool open) => Set(open, true); // �׷쿡�� ���� ������

    public void Set(bool open, bool force = false)
    {
        if (!force && isOpen == open) return;
        isOpen = open;

        if (content) content.SetActive(isOpen);

        if (arrow)
        {
            if (collapsedSprite && expandedSprite)
                arrow.sprite = isOpen ? expandedSprite : collapsedSprite;

            var rt = arrow.rectTransform;
            var e = rt.localEulerAngles;
            e.z = isOpen ? expandedZ : collapsedZ;
            rt.localEulerAngles = e;

            // ������ �ܻ� ����
            arrow.color = Color.white;
        }
    }
}
