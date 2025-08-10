from sport.models import TrainingClass


def get_training_class() -> TrainingClass:
    """
    Get all available training rooms
    @return training rooms
    """
    return TrainingClass.objects.all()
