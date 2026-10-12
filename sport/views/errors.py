from django.shortcuts import render


def handler404(request, exception, template_name="errors/404.html"):
    return render(request, template_name)


def handler500(request, template_name="errors/500.html"):
    return render(request, template_name)
