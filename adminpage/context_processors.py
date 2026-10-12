from django.conf import settings


def metrika(request):
    """
    Add yandex metrika counter id from settings, so "metrika.html" template can use it.
    """
    return {
        "YANDEX_METRIKA": settings.YANDEX_METRIKA
    }
