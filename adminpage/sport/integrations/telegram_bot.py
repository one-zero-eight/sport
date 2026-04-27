import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: int | str, text: str) -> bool:
    config = settings.TELEGRAM_BOT

    token = config.get("TOKEN")
    if not token:
        logger.warning("Telegram bot token is not configured")
        return False

    parse_mode = config.get("PARSE_MODE", "HTML")
    timeout = config.get("TIMEOUT_SECONDS", 10)

    proxies = config.get("PROXY")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=timeout,
            proxies=proxies,
        )
    except requests.RequestException:
        logger.exception("Failed to send Telegram message to chat_id=%s", chat_id)
        return False

    if not response.ok:
        logger.warning(
            "Telegram API returned %s for chat_id=%s",
            response.status_code,
            chat_id,
        )
        return False

    return True

