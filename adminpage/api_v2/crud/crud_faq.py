from collections import defaultdict
from sport.models import FAQElement

def get_faq_grouped_dict() -> dict:
    """
    Returns FAQ as:
    {
      "Category name": {
          "Question 1": "Answer 1",
          "Question 2": "Answer 2"
      },
      ...
    }
    """
    rows = FAQElement.objects.select_related("category").values_list(
        "category__name", "question", "answer"
    ).order_by("category__name", "id")

    result = defaultdict(dict)
    for cat_name, q, a in rows:
        result[cat_name][q] = a

    return dict(result)
