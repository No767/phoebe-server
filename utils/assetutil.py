import hashlib
import base64


def hash_bytes(data: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode("utf-8")
