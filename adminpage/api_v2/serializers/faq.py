from rest_framework import serializers

class FAQQuestionSerialazer(serializers.Serializer):
    question = serializers.CharField(help_text="answer", label="answer")

class FAQDictSerializer(serializers.Serializer):
    """
    { category: { question: answer } }
    """
    section = FAQQuestionSerialazer()

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
