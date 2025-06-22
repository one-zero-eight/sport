from django.urls import path, include, register_converter
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularSwaggerView, SpectacularJSONAPIView, SpectacularYAMLAPIView
from django.views.generic import RedirectView

from api.viewsets import (
    ProfileViewSet,
    EnrollmentViewSet,
    GroupViewSet,
    TrainingViewSet,
    AttendanceViewSet,
    CalendarViewSet,
    ReferenceViewSet,
    SelfSportViewSet,
    FitnessTestViewSet,
    MeasurementViewSet,
    SemesterViewSet,
    AnalyticsViewSet,
    MedicalGroupsViewSet,
)

class NegativeIntConverter:
    regex = '-?[0-9]+'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%d' % value

register_converter(NegativeIntConverter, 'negint')

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'enrollment', EnrollmentViewSet, basename='enrollment')
router.register(r'group', GroupViewSet, basename='group')
router.register(r'training', TrainingViewSet, basename='training')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'calendar', CalendarViewSet, basename='calendar')
router.register(r'reference', ReferenceViewSet, basename='reference')
router.register(r'selfsport', SelfSportViewSet, basename='selfsport')
router.register(r'fitnesstest', FitnessTestViewSet, basename='fitnesstest')
router.register(r'measurement', MeasurementViewSet, basename='measurement')
router.register(r'semester', SemesterViewSet, basename='semester')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'medical_groups', MedicalGroupsViewSet, basename='medical_groups')

urlpatterns = [
    path('', include(router.urls)),

    # OpenAPI schema & Swagger UI
    path('openapi.json', SpectacularJSONAPIView.as_view(), name='schema'),
    path('openapi.yaml', SpectacularYAMLAPIView.as_view(), name='schema-yaml'),
    path('docs', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger'),

    # Redirect from deprecated paths
    path('swagger.json', RedirectView.as_view(url="/api/openapi.json"), name='redirect-to-schema'),
    path('swagger.yaml', RedirectView.as_view(url="/api/openapi.yaml"), name='redirect-to-schema-yaml'),
    path('swagger/', RedirectView.as_view(url="/api/docs"), name='redirect-to-schema-swagger'),
    path('redoc/', RedirectView.as_view(url="/api/docs"), name='redirect-to-schema-swagger-from-redoc'),
]