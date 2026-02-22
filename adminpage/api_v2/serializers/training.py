from rest_framework import serializers


class TrainingInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    group_id = serializers.IntegerField(source="group__id")
    group_name = serializers.CharField()
    sport_id = serializers.IntegerField(source="group__sport__id")
    sport_name = serializers.CharField()
    training_class_id = serializers.IntegerField(source="training_class__id")
    training_class = serializers.CharField(source="training_class__name")
    capacity = serializers.IntegerField()
    is_club = serializers.BooleanField()
    custom_name = serializers.CharField()
    load = serializers.IntegerField()

