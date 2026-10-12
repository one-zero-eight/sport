from django.shortcuts import redirect
from django.conf import settings


def login_redirect(request):
    """
    Redirects users based on whether they are in the admins group
    """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    elif settings.OAUTH_CLIENT_ID == "?":
        return redirect("/admin/login/?next=/")
    else:
        return redirect('django_auth_adfs:login')
