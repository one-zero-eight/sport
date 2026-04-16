from django.contrib.admin.apps import AdminConfig


class SportAdminConfig(AdminConfig):
    default_site = 'sport.admin.site.SportAdminSite'

    def ready(self):
        super().ready()
        from django.contrib import admin
        from sport.admin.site import site
        admin.site = site  # hijack checks admin.site for User
        import adminpage.schema  # NOQA
