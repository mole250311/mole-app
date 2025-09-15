# routes/search.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
import requests
import urllib.parse

search_route = Blueprint("search", __name__)

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
HTTP_TIMEOUT = 8  # seconds
MAX_NAME_LEN = 200

def _ok(payload, code=200):
    return jsonify(payload), code

def _err(message: str, code: int, *, error_code: str = None, details: dict | None = None):
    body = {"ok": False, "error": message}
    if error_code:
        body["code"] = error_code
    if details:
        body["details"] = details
    return jsonify(body), code

def _fetch_sdf_by_name(name: str, record_type: str = "3d"):
    """
    record_type: '3d' 또는 '2d'
    성공 시 (text, status_code) 반환, 실패 시 예외 전파 또는 (None, status)
    """
    url = f"{PUBCHEM_BASE}/{urllib.parse.quote(name, safe='')}/record/SDF/?record_type={record_type}"
    resp = requests.get(
        url,
        headers={"User-Agent": "EduMolecule/1.0 (+search/from_name)"},
        timeout=HTTP_TIMEOUT,
    )
    return resp.text, resp.status_code

def _ensure_3d_coords(mol: Chem.Mol) -> Chem.Mol:
    """
    입력 mol에 좌표가 없으면 수소 추가 후 3D 임베딩 + UFF 최적화 수행
    """
    if mol is None:
        return None
    has_conformer = mol.GetNumConformers() > 0
    m = Chem.AddHs(mol)
    if not has_conformer:
        # 3D 좌표 생성
        if AllChem.EmbedMolecule(m, AllChem.ETKDG()) != 0:
            return None
    # UFF 최적화(실패해도 큰 문제는 아님)
    try:
        AllChem.UFFOptimizeMolecule(m, maxIters=500)
    except Exception:
        pass
    return m

@search_route.route("/from_name", methods=["GET"])
def from_name():
    name = request.args.get("name", "").strip()

    # ---------- 입력 검증 ----------
    if not name:
        return _err("name 파라미터가 필요합니다.", 400, error_code="MISSING_PARAM")
    if len(name) > MAX_NAME_LEN:
        return _err("name 길이가 너무 깁니다.", 400, error_code="PARAM_TOO_LONG", details={"max": MAX_NAME_LEN})

    # ---------- PubChem 조회 ----------
    try:
        sdf_text, status = _fetch_sdf_by_name(name, record_type="3d")
    except requests.Timeout:
        return _err("상위 서비스(PubChem) 타임아웃", 408, error_code="UPSTREAM_TIMEOUT")
    except requests.RequestException as e:
        return _err("상위 서비스 네트워크 오류", 502, error_code="UPSTREAM_NETWORK", details={"reason": str(e)})

    # 상태 매핑
    if status == 404:
        return _err("화합물을 찾을 수 없습니다.", 404, error_code="NOT_FOUND")
    if status == 429:
        return _err("요청이 너무 많습니다. 잠시 후 다시 시도하세요.", 429, error_code="RATE_LIMITED")
    if status >= 500:
        return _err("상위 서비스 오류", 502, error_code="UPSTREAM_ERROR", details={"upstream_status": status})
    if status != 200 or not sdf_text:
        return _err("유효하지 않은 상위 응답", 502, error_code="UPSTREAM_BAD_RESPONSE", details={"upstream_status": status})

    # ---------- RDKit 파싱 ----------
    # 3D SDF 파싱 시도
    mol = Chem.MolFromMolBlock(sdf_text, sanitize=True, removeHs=False)
    # 3D가 없거나 파싱 실패 시 2D 폴백
    if mol is None or mol.GetNumConformers() == 0:
        try:
            sdf2d_text, status2 = _fetch_sdf_by_name(name, record_type="2d")
            if status2 == 200 and sdf2d_text:
                mol = Chem.MolFromMolBlock(sdf2d_text, sanitize=True, removeHs=False)
        except Exception:
            # 폴백 조회 중 예외는 무시하고 아래에서 처리
            pass

    if mol is None:
        return _err("화합물 구조 파싱 실패", 422, error_code="PARSE_FAILED")

    # ---------- 좌표 확보(필요시 임베딩) ----------
    mol3d = _ensure_3d_coords(mol)
    if mol3d is None:
        return _err("3D 좌표 생성 실패", 422, error_code="EMBEDDING_FAILED")

    # ---------- 파생 정보 ----------
    try:
        mol_block = Chem.MolToMolBlock(mol3d)
        smiles = Chem.MolToSmiles(Chem.RemoveHs(mol3d))
        formula = rdMolDescriptors.CalcMolFormula(mol3d)
    except Exception as e:
        return _err("분자 정보 계산 실패", 422, error_code="DESCRIPTORS_FAILED", details={"reason": str(e)})

    return _ok({
        "ok": True,
        "name": name,
        "smiles": smiles,
        "formula": formula,
        "mol": mol_block,  # SDF mol block
    }, 200)
