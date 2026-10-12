from sport.models import MedicalGroup


def get_medical_groups():
    """
    Return the list of medical groups
    """
    query = MedicalGroup.objects.all()
    return list(query)
