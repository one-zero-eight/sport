from html import escape


def build_training_reminder_telegram_message(
    message: str,
    group_name: str,
    date: str,
    start_time: str,
    end_time: str,
    location: str,
    location_url: str,
) -> str:
    return message.format(
        group_name=escape(group_name),
        date=escape(date),
        start_time=escape(start_time),
        end_time=escape(end_time),
        location=escape(location),
        location_url=escape(location_url),
    )
