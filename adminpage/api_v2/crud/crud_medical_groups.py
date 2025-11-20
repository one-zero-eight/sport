from sport.models import MedicalGroup


def get_medical_groups():
    """
    Return the list of medical groups
    """
    query = MedicalGroup.objects.all()
    return list(query)

def get_medical_group_by_id(id: int) -> MedicalGroup:
    query = MedicalGroup.objects.filter(id=id)
    return query

def get_medical_group_by_name(name: str) -> MedicalGroup:
    query = MedicalGroup.objects.filter(name=name)
    return query
