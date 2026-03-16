from hashlib import sha256

def check_admin_auth(raw_credentials: str, expected_tg_id: str, expected_password: str) -> bool:
    try:
        tg_id, password = raw_credentials.split(":")
        return tg_id == expected_tg_id and hash_password(password) == hash_password(expected_password)
    except ValueError:
        return False
    
def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()