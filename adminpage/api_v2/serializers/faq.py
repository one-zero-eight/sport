from rest_framework import serializers

class FAQDictSerializer(serializers.Serializer):
    """
    { category: { question: answer } }
    """

    def to_representation(self, instance):
        return instance

    class Meta:
        swagger_schema_fields = {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": {
                    "type": "string"
                }
            }
        }
