from django.contrib import admin


class SportAdminSite(admin.AdminSite):
    site_header = 'Sport course administration'
    index_title = "InnoSport"
    site_title = "Admin panel"


site = SportAdminSite()
