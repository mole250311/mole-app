using TMPro;
using UnityEngine;

public class MoleculeHeaderController : MonoBehaviour
{
    public TMP_Text headerText;   // ���� �� ��(���� Proline ������ ��)

    public void SetHeader(string name)
    {
        if (headerText != null) headerText.text = name;
    }
}


