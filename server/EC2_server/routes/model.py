# routes/model.py
from __future__ import annotations
from flask import Blueprint, request, jsonify
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
import requests
import urllib.parse

model_route = Blueprint("model", __name__)

# -----------------------
# Config
# -----------------------
HTTP_TIMEOUT = 5
USER_AGENT = "EduMolecule/1.0 (+model/compose)"
MAX_ATOMS = 200
MAX_BONDS = 400
ALLOWED_BOND_TYPES = {1: Chem.BondType.SINGLE, 2: Chem.BondType.DOUBLE, 3: Chem.BondType.TRIPLE}

# -----------------------
# Helpers
# -----------------------
def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code

def _err(msg: str, code: int, *, error_code: str = None, details: dict | None = None):
    body = {"ok": False, "error": msg}
    if error_code: body["code"] = error_code
    if details: body["details"] = details
    return jsonify(body), code

def _valid_symbol(sym: str) -> bool:
    if not sym or not isinstance(sym, str): return False
    try:
        # 유효하지 않으면 0 또는 예외가 남
        return Chem.GetPeriodicTable().GetAtomicNumber(sym) > 0
    except Exception:
        return False

# -----------------------
# Compose molecule
# -----------------------
@model_route.route("/compose", methods=["POST"])
def compose_model():
    data = request.get_json(silent=True) or None
    if not data:
        return _err("요청 본문(JSON)이 필요합니다.", 400, error_code="MISSING_BODY")

    atoms = data.get("atoms")
    bonds = data.get("bonds")
    if not isinstance(atoms, list) or not isinstance(bonds, list):
        return _err("atoms, bonds는 리스트여야 합니다.", 400, error_code="INVALID_PARAM")

    if len(atoms) == 0:
        return _err("최소 1개 이상의 atom이 필요합니다.", 400, error_code="MISSING_ATOMS")
    if len(atoms) > MAX_ATOMS or len(bonds) > MAX_BONDS:
        return _err("분자 크기 제한 초과", 400, error_code="TOO_LARGE",
                    details={"max_atoms": MAX_ATOMS, "max_bonds": MAX_BONDS})

    # ------- 원자/결합 입력 검증 -------
    atom_id_map = {}
    seen_ids = set()
    for i, atom in enumerate(atoms):
        if not isinstance(atom, dict) or "id" not in atom or "element" not in atom:
            return _err("atom 항목은 {id, element}를 포함해야 합니다.", 400, error_code="INVALID_ATOM",
                        details={"index": i, "atom": atom})
        aid = atom["id"]
        elem = atom["element"]
        if aid in seen_ids:
            return _err("중복된 atom id가 있습니다.", 400, error_code="DUP_ATOM_ID", details={"id": aid})
        if not _valid_symbol(elem):
            return _err("유효하지 않은 원소 심볼입니다.", 400, error_code="INVALID_ELEMENT",
                        details={"element": elem})
        seen_ids.add(aid)

    for j, bond in enumerate(bonds):
        if not isinstance(bond, dict) or "atom1" not in bond or "atom2" not in bond:
            return _err("bond 항목은 {atom1, atom2[, bondType]}을 포함해야 합니다.",
                        400, error_code="INVALID_BOND", details={"index": j, "bond": bond})
        a1, a2 = bond["atom1"], bond["atom2"]
        if a1 == a2:
            return _err("자기 자신과의 결합은 허용되지 않습니다.", 400, error_code="SELF_BOND", details={"atom": a1})
        bt = int(bond.get("bondType", 1))
        if bt not in ALLOWED_BOND_TYPES:
            return _err("허용되지 않는 bondType입니다. (1,2,3 허용)", 400, error_code="INVALID_BOND_TYPE",
                        details={"bondType": bt})

    # ------- RWMol 구성 -------
    try:
        mol = Chem.RWMol()
        for atom in atoms:
            rd_atom = Chem.Atom(atom["element"])
            idx = mol.AddAtom(rd_atom)
            atom_id_map[atom["id"]] = idx

        for bond in bonds:
            a1 = bond["atom1"]; a2 = bond["atom2"]
            if a1 not in atom_id_map or a2 not in atom_id_map:
                return _err("존재하지 않는 atom id를 참조했습니다.", 400, error_code="INVALID_BOND_REF",
                            details={"atom1": a1, "atom2": a2})
            bond_order = ALLOWED_BOND_TYPES[int(bond.get("bondType", 1))]
            mol.AddBond(atom_id_map[a1], atom_id_map[a2], bond_order)

        mol = mol.GetMol()
    except Exception as e:
        return _err("분자 구성에 실패했습니다.", 422, error_code="BUILD_FAILED", details={"reason": str(e)})

    # ------- 정합성/3D 좌표 생성 -------
    try:
        Chem.SanitizeMol(mol)  # valence, aromaticity 등
    except Exception as e:
        return _err("분자 정합성 검증(Sanitize) 실패", 422, error_code="SANITIZE_FAILED", details={"reason": str(e)})

    try:
        molH = Chem.AddHs(mol)
        # 임베딩 (ETKDG: 빠르고 안정적)
        if AllChem.EmbedMolecule(molH, AllChem.ETKDG()) != 0:
            return _err("3D 임베딩 실패", 422, error_code="EMBEDDING_FAILED")
        # 에너지 최소화 (실패해도 큰 문제는 아님)
        try:
            AllChem.UFFOptimizeMolecule(molH, maxIters=500)
        except Exception as e:
            # 최적화 실패는 경고 수준으로 세부만 기재
            opt_error = str(e)
        else:
            opt_error = None
    except Exception as e:
        return _err("3D 좌표 생성 과정에서 오류", 422, error_code="EMBEDDING_FAILED", details={"reason": str(e)})

    # ------- 파생 정보 -------
    try:
        mol_block = Chem.MolToMolBlock(molH)
        smiles = Chem.MolToSmiles(Chem.RemoveHs(molH))
        formula = rdMolDescriptors.CalcMolFormula(molH)
    except Exception as e:
        return _err("분자 정보 계산 실패", 422, error_code="DESCRIPTORS_FAILED", details={"reason": str(e)})

    # ------- (옵션) PubChem에서 IUPAC 이름 조회 (비차단적으로 빠르게) -------
    name = "Unknown"
    try:
        encoded_smiles = urllib.parse.quote(smiles, safe="")
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{encoded_smiles}/property/IUPACName/JSON"
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=HTTP_TIMEOUT)
        if resp.status_code == 200:
            js = resp.json()
            name = js["PropertyTable"]["Properties"][0].get("IUPACName", "Unknown")
        # 200이 아니면 그냥 이름은 Unknown 유지 (응답 지연 방지)
    except requests.Timeout:
        # 이름만 포기하고 본문 성공 반환
        pass
    except Exception:
        pass

    result = {
        "ok": True,
        "mol": mol_block,
        "smiles": smiles,
        "formula": formula,
        "name": name
    }
    if opt_error:
        # 최적화 실패가 있었던 경우만 부가정보로 전달(성공에는 영향 X)
        result["warnings"] = [{"code": "OPTIMIZE_FAILED", "message": "에너지 최적화에 실패하여 초기 좌표를 사용했습니다."}]

    return _ok(result)
