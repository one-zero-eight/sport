from sport.models import FAQCategory, FAQElement


def get_faq() -> list:
    """
    Get FAQ
    """
    result = []
    for i in FAQCategory.objects.all():
        result.append({'name': i.name, 'values': list(FAQElement.objects.filter(category__name=i.name))})
    return result
