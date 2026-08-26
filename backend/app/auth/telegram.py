from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl


class TelegramAuthError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ValidatedInitData:
    user: dict[str, Any]
    auth_date: int
    fields: dict[str, str]


def validate_init_data(
    raw_init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 300,
    clock_skew_seconds: int = 30,
    max_length: int = 8192,
) -> ValidatedInitData:
    if not raw_init_data or len(raw_init_data) > max_length:
        raise TelegramAuthError("invalid init data")

    try:
        pairs = parse_qsl(raw_init_data, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise TelegramAuthError("invalid init data") from exc

    if len({key for key, _ in pairs}) != len(pairs):
        raise TelegramAuthError("duplicate init data field")

    fields = dict(pairs)
    received_hash = fields.pop("hash", None)
    if not received_hash or len(received_hash) != 64:
        raise TelegramAuthError("invalid hash")

    data_check_string = "\n".join(
        f"{key}={fields[key]}" for key in sorted(fields)
    )
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    expected_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise TelegramAuthError("invalid hash")

    try:
        auth_date = int(fields["auth_date"])
    except (KeyError, ValueError) as exc:
        raise TelegramAuthError("invalid auth date") from exc

    age = int(time.time()) - auth_date
    if age > max_age_seconds or age < -clock_skew_seconds:
        raise TelegramAuthError("expired init data")

    try:
        user = json.loads(fields["user"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise TelegramAuthError("invalid user") from exc

    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        raise TelegramAuthError("invalid user")

    return ValidatedInitData(user=user, auth_date=auth_date, fields=fields)
