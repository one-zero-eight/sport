from sport.models import FAQCategory, FAQElement


def get_faq() -> list:
    """
    Get FAQ
    """
    result = []
    for i in FAQCategory.objects.all():
        result.append({'name': i.name, 'values': list(FAQElement.objects.filter(category__name=i.name))})
    return result


def get_faq_as_dict() -> dict:
    """
    Get FAQ as a dictionary with question as key and answer as value
    Uses data from the existing get_faq() function
    """
    result = {}
    faq_data = get_faq()  # Use existing FAQ function
    
    for category in faq_data:
        for faq_element in category['values']:
            result[faq_element.question] = faq_element.answer
    
    return result
