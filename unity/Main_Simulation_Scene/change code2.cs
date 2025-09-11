using TMPro;
using UnityEngine;

public class MoleculeRow : MonoBehaviour
{
    public MoleculeHeaderController header;   // A���� ���� ��Ʈ�ѷ� �ֱ�
    public TMP_Text rowText;                  // �� ��ư�� ���̴� �ؽ�Ʈ

    public void OnClick()
    {
        if (header != null && rowText != null)
            header.SetHeader(rowText.text);
    }
}

