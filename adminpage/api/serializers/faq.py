from rest_framework import serializers


class FAQDictSerializer(serializers.Serializer):
    """
    Serializer for FAQ dictionary format where questions are keys and answers are values
    """
    def to_representation(self, instance):
        """
        Convert FAQ dictionary to proper representation
        """
        return instance 