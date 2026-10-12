"""adminpage URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from sport.admin.site import site

# TODO: remove when not needed
# from django.http import JsonResponse
# def show(request):
#     data = dict(
#         [
#             (key, str(value)) for key, value in request.META.items()
#         ]
#     )
#     data.update({
#         "scheme": str(request.scheme),
#     })
#     return JsonResponse(data)

handler404 = "sport.views.errors.handler404"
handler500 = "sport.views.errors.handler500"

urlpatterns = [
    path(settings.PREFIX, include([
        path("", include("sport.urls")),
        # only /metrics
        path('', include('django_prometheus.urls')),
        path('admin/', site.urls),
        path('oauth2/', include('django_auth_adfs.urls')),

        path("api/", include("api.urls")),
        path("media/", include('media.urls')),
        path('hijack/', include('hijack.urls')),
    ]))
] \
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
