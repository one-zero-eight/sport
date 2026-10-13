from sport.models import TrainingClass


def get_training_class() -> list[TrainingClass]:
    """
    Get all available training rooms
    @return training rooms
    """
    query = TrainingClass.objects.all()
    return list(query)
