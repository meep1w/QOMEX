# utils.py
import secrets, string

def gen_click_id(n: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits + "_-"
    return ''.join(secrets.choice(alphabet) for _ in range(n))
