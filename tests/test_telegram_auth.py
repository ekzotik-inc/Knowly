import hashlib
import hmac
import json
import time
from urllib.parse import quote

import pytest

from app.auth.telegram import TelegramAuthError, validate_init_data

BOT_TOKEN = "123456:TEST_TOKEN"


def make_init_data(*, auth_date: int | None = None, user_id: int = 123456789) -> str:
    fields = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "AAE-test-query",
        "user": json.dumps(
            {"id": user_id, "first_name": "Анна", "username": "anna"},
            separators=(",", ":"),
        ),
    }
    check = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return "&".join(f"{key}={quote(value, safe='')}" for key, value in (*fields.items(), ("hash", digest)))


def test_valid_init_data():
    result = validate_init_data(make_init_data(), BOT_TOKEN)
    assert result.user["id"] == 123456789
    assert result.user["first_name"] == "Анна"


def test_modified_payload_is_rejected():
    raw = make_init_data().replace("anna", "attacker")
    with pytest.raises(TelegramAuthError):
        validate_init_data(raw, BOT_TOKEN)


def test_expired_payload_is_rejected():
    raw = make_init_data(auth_date=int(time.time()) - 301)
    with pytest.raises(TelegramAuthError):
        validate_init_data(raw, BOT_TOKEN, max_age_seconds=300)


def test_duplicate_key_is_rejected():
    raw = make_init_data() + "&auth_date=1"
    with pytest.raises(TelegramAuthError):
        validate_init_data(raw, BOT_TOKEN)
