import logging
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _normalize_bearer_token(token: str | None) -> str | None:
    if not token:
        return None

    token = token.strip()
    if not token:
        return None

    if token.lower().startswith("bearer "):
        return token

    return f"Bearer {token}"


def _read_nested(data: dict, path: tuple[str, ...]):
    value = data
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def get_student_telegram_id(email: str) -> int | None:
    config = settings.INNOHASSLE_ACCOUNTS_API

    if not config.get("ENABLED", False):
        return None

    auth_header = _normalize_bearer_token(config.get("TOKEN"))
    if not auth_header:
        logger.warning("InNoHassle Accounts API token is not configured")
        return None

    base_url = config.get("BASE_URL", "").rstrip("/")
    path_template = config.get("BY_INNOMAIL_PATH", "/users/by-innomail/{email}")
    timeout = config.get("TIMEOUT_SECONDS", 10)
    email_encoded = quote(email, safe="")
    url = f"{base_url}{path_template.format(email=email_encoded)}"

    try:
        response = requests.get(
            url,
            headers={
                "accept": "application/json",
                "Authorization": auth_header,
            },
            timeout=timeout,
        )
    except requests.RequestException:
        logger.exception("Failed to fetch user data from InNoHassle Accounts API")
        return None

    if response.status_code == 404:
        return None

    if not response.ok:
        logger.warning(
            "InNoHassle Accounts API returned %s for email %s",
            response.status_code,
            email,
        )
        return None

    try:
        data = response.json()
    except ValueError:
        logger.warning("InNoHassle Accounts API returned non-JSON response")
        return None

    tg_path = tuple(config.get("TG_ID_PATH", ("telegram_info", "id")))
    tg_id = _read_nested(data, tg_path)
    if tg_id is None:
        tg_id = _read_nested(data, ("telegram_update_data", "id"))

    if isinstance(tg_id, int):
        return tg_id

    if isinstance(tg_id, str) and tg_id.isdigit():
        return int(tg_id)

    return None

