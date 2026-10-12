from django.apps import AppConfig


class SportConfig(AppConfig):
    name = 'sport'

    def ready(self) -> None:
        # Register signals
        import sport.signals  # noqa: F401
