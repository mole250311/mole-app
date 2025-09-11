using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class NavAccordionHighlighter : MonoBehaviour
{
    [System.Serializable]
    public class Item
    {
        public Button button;            // ���� ��ư (��ؼ�/�ؼ�/��)
        public TMP_Text label;           // ���� ��
        public Image icon;               // ���� ������
        public RectTransform content;    // ������ �г�(���� ����Ʈ ��Ʈ)
    }

    public List<Item> items = new List<Item>();

    public Color selected = new Color32(0x3D, 0x6C, 0xFF, 0xFF); // �Ķ�
    public Color normal = new Color32(0xA6, 0xAE, 0xBD, 0xFF); // ȸ��

    // ���� ���� ���� �׸� �ε���(-1 = ����)
    private int selectedIndex = -1;

    // ���� ��ư ����(�ڵ� �����)
    private readonly Dictionary<Button, TMP_Text> subBtnToText = new Dictionary<Button, TMP_Text>();

    void Awake()
    {
        // ���� ��ư ������ ����
        for (int i = 0; i < items.Count; i++)
        {
            int idx = i;
            var it = items[i];

            if (!it.label) it.label = it.button.GetComponentInChildren<TMP_Text>(true);
            if (!it.icon)
            {
                foreach (var img in it.button.GetComponentsInChildren<Image>(true))
                    if (img.gameObject != it.button.gameObject) { it.icon = img; break; }
            }

            it.button.transition = Selectable.Transition.None;
            it.button.onClick.RemoveAllListeners();   // Ȥ�� �����ִ� �� ����(�ߺ� ����)
            it.button.onClick.AddListener(() => Toggle(idx));
        }

        // ���� ��ư �ڵ� ����(������)
        AutoBindSubButtons();
    }

    void Start()
    {
        // ó�� ����: ���� ����, ��� �ؽ�Ʈ ���� normal��
        CollapseAll();
        ApplyNormalToAllTexts();
    }

    // ���� ��ư ���
    public void Toggle(int index)
    {
        if (selectedIndex == index)
        {
            // ���� �׸� �ٽ� Ŭ�� �� ���� + ���� �ʱ�ȭ
            SetItemVisual(index, false);
            if (items[index].content)
            {
                ResetSubTexts(items[index].content);
                items[index].content.gameObject.SetActive(false);
            }
            selectedIndex = -1;
        }
        else
        {
            // ���� ���� �׸� �ݱ�
            if (selectedIndex != -1)
            {
                SetItemVisual(selectedIndex, false);
                if (items[selectedIndex].content)
                {
                    ResetSubTexts(items[selectedIndex].content);
                    items[selectedIndex].content.gameObject.SetActive(false);
                }
            }
            // �� �׸� ����
            selectedIndex = index;
            SetItemVisual(index, true);
            if (items[index].content) items[index].content.gameObject.SetActive(true);
        }

        // ���̾ƿ� ����(��ħ ����)
        LayoutRebuilder.ForceRebuildLayoutImmediate(GetComponent<RectTransform>());
    }

    // ���� ��ư Ŭ�� �� ���̶���Ʈ(���� 1���� �Ķ�)
    private void OnSubItemClicked(Button btn)
    {
        // ���� �׷�(���� ���� content) ���� ���� �ؽ�Ʈ�� ��� normal��
        if (selectedIndex != -1 && items[selectedIndex].content)
            ResetSubTexts(items[selectedIndex].content);

        // ��� ���� ������ �Ķ�
        if (subBtnToText.TryGetValue(btn, out var t) && t) t.color = selected;
    }

    private void SetItemVisual(int i, bool on)
    {
        var it = items[i];
        if (it.label) it.label.color = on ? selected : normal;
        if (it.icon) it.icon.color = on ? selected : normal;
    }

    private void ResetSubTexts(RectTransform root)
    {
        if (!root) return;
        var texts = root.GetComponentsInChildren<TMP_Text>(true);
        foreach (var t in texts) t.color = normal;
    }

    private void CollapseAll()
    {
        for (int i = 0; i < items.Count; i++)
        {
            var it = items[i];
            if (it.content) it.content.gameObject.SetActive(false);
            SetItemVisual(i, false);
        }
        selectedIndex = -1;
    }

    private void ApplyNormalToAllTexts()
    {
        // ����
        foreach (var it in items)
        {
            if (it.label) it.label.color = normal;
            if (it.icon) it.icon.color = normal;
            if (it.content) ResetSubTexts(it.content);
        }
        // ������ġ: �� ������Ʈ ������ ��� TMP_Text�� �ѹ� �� ȸ������
        foreach (var t in GetComponentsInChildren<TMP_Text>(true))
            t.color = normal;
    }

    private void AutoBindSubButtons()
    {
        subBtnToText.Clear();
        foreach (var it in items)
        {
            if (!it.content) continue;
            var childButtons = it.content.GetComponentsInChildren<Button>(true);
            foreach (var b in childButtons)
            {
                // Button�� �޸� �ؽ�Ʈ �ڵ� ����
                TMP_Text txt = b.GetComponentInChildren<TMP_Text>(true);
                if (txt) subBtnToText[b] = txt;

                // �ߺ� ������ ����
                b.onClick.RemoveListener(() => OnSubItemClicked(b)); // RemoveListener�� ���� �񱳴� �� �ǹǷ� �Ʒ� ��� ��� �Ұ�
                // �����ϰ� ��� ���� �� �ٽ� ����
                b.onClick.RemoveAllListeners();
                b.onClick.AddListener(() => OnSubItemClicked(b));
            }
        }
    }

    // �ܺο��� ���� �ʱ�ȭ�ϰ� ���� ��
    public void SelectNone()
    {
        CollapseAll();
        ApplyNormalToAllTexts();
        LayoutRebuilder.ForceRebuildLayoutImmediate(GetComponent<RectTransform>());
    }
}


