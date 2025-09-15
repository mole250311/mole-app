import os, hashlib, hmac, base64
from typing import Tuple

# 기본 반복 횟수 (환경변수로 조정 가능)
PBKDF2_ITER = int(os.getenv("PBKDF2_ITER", "100000"))
SALT_LEN = int(os.getenv("PBKDF2_SALT_LEN", "16"))
DKLEN = 32

def hash_password(password: str) -> Tuple[str, str, int]:
    """
    PBKDF2-SHA256 알고리즘으로 비밀번호 해싱
    :return: (base64_hash, base64_salt, iterations)
    """
    if not password:
        raise ValueError("비밀번호는 비어 있을 수 없습니다.")

    salt_bytes = os.urandom(SALT_LEN)
    hashed_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITER,
        dklen=DKLEN
    )

    return (
        base64.b64encode(hashed_bytes).decode(),
        base64.b64encode(salt_bytes).decode(),
        PBKDF2_ITER,
    )

def verify_password(password: str, stored_hash: str, stored_salt: str, iterations: int = PBKDF2_ITER) -> bool:
    """
    입력한 비밀번호가 저장된 해시와 일치하는지 검증
    """
    if not password:
        return False

    salt_bytes = base64.b64decode(stored_salt.encode())
    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        iterations,
        dklen=DKLEN
    )
    return hmac.compare_digest(
        base64.b64encode(new_hash).decode(),
        stored_hash
    )
