from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.cache import never_cache

SIDEBAR_SECTIONS = {
    "Accounts": ["accounts.User", "auth.Group", "sport.Student", "sport.Trainer"],
    "Schedule": ["sport.Sport", "sport.Group", "sport.Training", "sport.Semester", "sport.Schedule"],
    "Review": ["sport.SelfSportReport", "sport.MedicalGroupReference", "sport.Reference"],
    "Fitness test": [
        "sport.FitnessTestExercise", "sport.FitnessTestGrading", "sport.FitnessTestResult",
        "sport.FitnessTestSession", "sport.Measurement", "sport.MeasurementResult", "sport.MeasurementSession",
    ],
    "Info": [
        "sport.FAQCategory", "sport.FAQElement", "sport.MedicalGroup",
        "sport.StudentStatus", "sport.Course", "sport.TrainingClass", "sport.SelfSportType",
    ],
    "Sport": [],  # All other registered models
}


class SportAdminSite(admin.AdminSite):
    site_header = "InnoSport"
    index_title = "InnoSport"
    site_title = "InnoSport"

    login_form = AuthenticationForm  # Allow college/students to log in using password

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if app_label is not None:
            return app_list

        sections = {}
        for name in SIDEBAR_SECTIONS:
            slug = slugify(name)
            sections[slug] = {
                "name": name,
                "app_label": slug,
                "app_url": f"{reverse('admin:index')}#app-{slug}",
                "has_module_perms": True,
                "models": [],
            }

        model_sections = {
            model: slugify(name)
            for name, models in SIDEBAR_SECTIONS.items()
            for model in models
        }
        for app in app_list:
            for model in app["models"]:
                section = model_sections.get(
                    f"{app['app_label']}.{model['object_name']}", app["app_label"],
                )
                sections.setdefault(section, {**app, "models": []})["models"].append(model)

        return [section for section in sections.values() if section["models"]]

    @method_decorator(never_cache)
    @login_not_required
    def login(self, request, extra_context=None):
        # Allow college/students to log in using password
        if request.method == "GET" and request.user.is_active and not request.user.is_staff:
            return HttpResponseRedirect("/")
        return super().login(request, extra_context)


site = SportAdminSite()
