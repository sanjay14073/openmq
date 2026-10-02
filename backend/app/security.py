import hashlib
import secrets
from fastapi import Header, HTTPException
from .config import settings

def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def verify_secret(value: str, expected_hash: str) -> bool:
    return secrets.compare_digest(hash_secret(value), expected_hash)

def require_admin(x_admin_key: str | None = Header(default=None)):
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")

def require_client_headers(
    x_client_id: str | None = Header(default=None),
    x_client_secret: str | None = Header(default=None),
):
    if not x_client_id or not x_client_secret:
        raise HTTPException(status_code=401, detail="X-Client-Id and X-Client-Secret are required")
    return x_client_id, x_client_secret
