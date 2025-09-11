import os, hashlib, hmac, base64

def hash_password(password: str) -> tuple[str, str]:
    """
    PBKDF2-SHA256 알고리즘으로 비밀번호 해싱
    :return: (base64_hash, base64_salt)
    """
    salt_bytes = os.urandom(16)  # 예측 불가 16바이트 salt
    hashed_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        100_000,  # 반복 횟수
        dklen=32
    )

    return base64.b64encode(hashed_bytes).decode(), base64.b64encode(salt_bytes).decode()


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """
    입력한 비밀번호가 저장된 해시와 일치하는지 검증
    """
    salt_bytes = base64.b64decode(stored_salt.encode())
    new_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        100_000,
        dklen=32
    )
    return hmac.compare_digest(
        base64.b64encode(new_hash).decode(),
        stored_hash
    )