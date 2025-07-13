from rest_framework import serializers

from sport.models import SelfSportReport, SelfSportType


class SelfSportTypes(serializers.ModelSerializer[SelfSportType]):
    class Meta:
        model = SelfSportType
        fields = (
            'pk',
            'name',
            'application_rule',
        )


class SelfSportReportUploadSerializer(serializers.ModelSerializer[SelfSportReport]):
    # image = serializers.ImageField(allow_empty_file=False, required=False)
    link = serializers.URLField(required=True)
    training_type = serializers.PrimaryKeyRelatedField(
        queryset=SelfSportType.objects.filter(
            is_active=True,
        ).all()
    )
    # start = serializers.DateTimeField(required=True)
    # end = serializers.DateTimeField(required=True)
    hours = serializers.IntegerField()
    student_comment = serializers.CharField(required=False)
    parsed_data = serializers.JSONField(required=False)

    class Meta:
        model = SelfSportReport
        fields = (
            'link',
            'hours',
            'training_type',
            'student_comment',
            'parsed_data'
        )

class ParseStrava(serializers.Serializer):
    link = serializers.URLField(required=True)

class ParsedStravaSerializer(serializers.Serializer):
    training_type = serializers.CharField()
    pace = serializers.CharField(required=False)
    speed = serializers.CharField(required=False)
    distance_km = serializers.IntegerField()
    hours = serializers.IntegerField()
    approved = serializers.BooleanField()
