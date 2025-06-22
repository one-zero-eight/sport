from django.apps import AppConfig


class SportConfig(AppConfig):
    name = 'sport'

    def ready(self) -> None:
        import sport.signals  # noqa

        # TODO: resolve in a better way
        # if the database doesn't have a migration
        # on Group, these changes will cause an error
        # preventing database migration
        try:
            sport.signals.get_or_create_trainer_group()
            sport.signals.get_or_create_student_group()
        except:
            pass
