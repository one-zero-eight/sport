from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class SportAdminSite(admin.AdminSite):
    site_header = "InnoSport"
    index_title = "InnoSport"
    site_title = "InnoSport"

    login_form = AuthenticationForm  # Allow college/students to log in using password

    @method_decorator(never_cache)
    @login_not_required
    def login(self, request, extra_context=None):
        # Allow college/students to log in using password
        if request.method == "GET" and request.user.is_active and not request.user.is_staff:
            return HttpResponseRedirect("/")
        return super().login(request, extra_context)


site = SportAdminSite()
