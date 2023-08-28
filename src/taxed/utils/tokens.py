import secrets
import string


def generate_token(chars: int = 16):
    return ''.join(secrets.choice(
        string.ascii_letters + string.digits) for _ in range(chars))
