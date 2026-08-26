from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: uuid.UUID, secret: str, ttl_seconds: int) -> str:
    payload = _b64(json.dumps({"sub": str(user_id), "exp": int(time.time()) + ttl_seconds}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def verify_access_token(token: str, secret: str) -> uuid.UUID | None:
    try:
        payload, received_signature = token.split(".", 1)
        expected_signature = _b64(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expected_signature, received_signature):
            return None
        data = json.loads(_unb64(payload))
        if int(data["exp"]) <= int(time.time()):
            return None
        return uuid.UUID(data["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return None
