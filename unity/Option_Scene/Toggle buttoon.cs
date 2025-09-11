using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;

public class ToggleVisual : MonoBehaviour
{
    [Header("필수")]
    public Toggle toggle;
    public Image background;
    public RectTransform handle;
    public Image handleImage;

    [Header("색/스프라이트")]
    public Color onColor = new Color(0.25f, 0.5f, 1f);
    public Color offColor = Color.gray;
    public Sprite onHandleSprite;
    public Sprite offHandleSprite;

    [Header("핸들 위치 (로컬 앵커드)")]
    public Vector2 handleOnPos = new Vector2(10, 0);
    public Vector2 handleOffPos = new Vector2(-10, 0);

    [Header("상태 저장 옵션")]
    public bool usePersistence = true;         // PlayerPrefs에 저장할지
    public string prefsKey = "Toggle_Generic"; // 저장 키
    public bool defaultOn = true;              // 저장값 없을 때 기본값

    [Header("동작 옵션")]
    public bool interactive = true;            // 읽기전용 모드(보기용)면 false
    public UnityEvent<bool> onToggle;          // 선택: 외부 로직 호출(음소거 등)

    void Start()
    {
        if (!toggle) toggle = GetComponent<Toggle>();
        if (toggle == null) { Debug.LogError("[ToggleVisual] Toggle가 없습니다."); return; }

        // 읽기전용 모드
        toggle.interactable = interactive;

        // 저장된 값 불러오기
        bool isOn = usePersistence
            ? PlayerPrefs.GetInt(prefsKey, defaultOn ? 1 : 0) == 1
            : defaultOn;

        // 초기값 적용(콜백 호출 없이)
        toggle.SetIsOnWithoutNotify(isOn);
        UpdateToggleUI(isOn);

        // 리스너 연결
        toggle.onValueChanged.RemoveAllListeners();
        toggle.onValueChanged.AddListener(HandleChanged);
    }

    void HandleChanged(bool isOn)
    {
        UpdateToggleUI(isOn);

        // 선택: 외부 이벤트 호출(원하면 여기다 음소거/설정 반영 등 연결)
        onToggle?.Invoke(isOn);

        // 저장
        if (usePersistence)
        {
            PlayerPrefs.SetInt(prefsKey, isOn ? 1 : 0);
            PlayerPrefs.Save();
        }
    }

    void UpdateToggleUI(bool isOn)
    {
        if (background) background.color = isOn ? onColor : offColor;
        if (handle) handle.anchoredPosition = isOn ? handleOnPos : handleOffPos;
        if (handleImage) handleImage.sprite = isOn ? onHandleSprite : offHandleSprite;
    }

    // 코드로 상태만 바꾸고 싶을 때(콜백까지 실행)
    public void Set(bool isOn)
    {
        if (!toggle) return;
        toggle.isOn = isOn;
    }
}

