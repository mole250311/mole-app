using System.Collections;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

public class MoleculeSender : MonoBehaviour
{
    public Mol3DRenderer molRenderer;
    public AtomSpawner atomSpawner;
    public BondDrawer bondDrawer;
    public EraserManager eraserManager;
    /*public string severUrl;*/
    //private string serverUrl = PlayerPrefs.GetString("ServerUrl");
    private string serverUrl;

    public GameObject Mol_Texts;
    //public GameObject Buttons;
    //public GameObject BackDrawButton;

    public GameObject errorUI;
    public TextMeshProUGUI errorText;

    public TextMeshProUGUI nameText;
    public TextMeshProUGUI smilesText;
    public TextMeshProUGUI formulaText;

    [System.Serializable]
    public class AtomJson
    {
        public int id;
        public string element;
    }

    [System.Serializable]
    public class BondJson
    {
        public int atom1;
        public int atom2;
        public int bondType; // ✅ 이중결합 정보 포함
    }

    [System.Serializable]
    public class MoleculeJson
    {
        public System.Collections.Generic.List<AtomJson> atoms;
        public System.Collections.Generic.List<BondJson> bonds;
    }

    // 👇 서버 응답 파싱 클래스
    [System.Serializable]
    public class MoleculeResponse
    {
        public string mol;
        public string smiles;
        public string formula;
        public string name;
    }

    public void SendMoleculeToServer()
    {
        errorUI.SetActive(false);
        errorText.text = "";
        StartCoroutine(SendDataCoroutine());
    }
    private IEnumerator SendDataCoroutine()
    {
        MoleculeJson molecule = new MoleculeJson
        {
            atoms = new System.Collections.Generic.List<AtomJson>(),
            bonds = new System.Collections.Generic.List<BondJson>()
        };

        // ✅ 원자 정보 추가
        foreach (var a in atomSpawner.atoms)
        {
            molecule.atoms.Add(new AtomJson { id = a.id, element = a.element });
        }

        // ✅ 결합 정보 추가 (이중결합 포함)
        foreach (var b in bondDrawer.bonds)
        {
            molecule.bonds.Add(new BondJson
            {
                atom1 = b.atomId1,
                atom2 = b.atomId2,
                bondType = b.bondType // 🎯 여기에 핵심!
            });
        }

        // ✅ JSON 변환
        string json = JsonUtility.ToJson(molecule);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

        serverUrl = PlayerPrefs.GetString("ServerUrl");

        //"http://127.0.0.1:5000/from_json" 로컬 서버 주소
        //using (UnityWebRequest request = UnityWebRequest.Put(severUrl + "/from_json", bodyRaw))
        using (UnityWebRequest request = UnityWebRequest.Put(serverUrl + "/model/compose", bodyRaw))
        {
            request.method = UnityWebRequest.kHttpVerbPOST;
            request.SetRequestHeader("Content-Type", "application/json");

            request.certificateHandler = new BypassCertificate(); // ✅ 여기만 추가!

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("서버 요청 실패: " + request.error);
                if (request.error == "Cannot connect to destination host")
                {
                    errorUI.SetActive(true);
                    errorText.text = "서버연결 실패";
                }
                else if (request.error == "HTTP/1.1 500 Internal Server Error")
                {
                    errorUI.SetActive(true);
                    errorText.text = "존재하지 않는 구조";
                }
            }
            else
            {
                // 🎯 응답 JSON 파싱
                MoleculeResponse response = JsonUtility.FromJson<MoleculeResponse>(request.downloadHandler.text);

                if (!string.IsNullOrEmpty(response.mol))
                {
                    // 3D 모델 렌더링
                    molRenderer.RenderMol(response.mol);

                    // UI 텍스트에 표시 (인스펙터에서 연결되어 있다면)
                    if (nameText != null) nameText.text = "Name: " + response.name;
                    if (smilesText != null) smilesText.text = "SMILES: " + response.smiles;
                    if (formulaText != null) formulaText.text = "Formula: " + response.formula;

                    //BackDrawButton.SetActive(true);
                    Mol_Texts.SetActive(true);
                    //Buttons.SetActive(false);

                    //eraserManager.ResetAll(); // 그림지우기
                }
                else
                {
                    Debug.LogWarning("Mol 데이터가 비어 있습니다.");
                }
            }
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
