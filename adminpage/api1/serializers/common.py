from typing import Type, Optional, Union, Iterable

from rest_framework import serializers

SerializerClass = Type[serializers.Serializer]


class EmptySerializer(serializers.Serializer):
    pass


class NotFoundSerializer(serializers.Serializer):
    detail = serializers.ReadOnlyField(default="Not found")


class InbuiltErrorSerializer(serializers.Serializer):
    detail = serializers.ReadOnlyField()


class ErrorSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    detail = serializers.CharField()


def get_error_serializer(
        reference_name: str,
        error_code: Optional[int] = None,
        error_description: str = "",
        additional_data: SerializerClass = EmptySerializer,
        additional_data_many: bool = False,
) -> SerializerClass:
    class ErrorResponseSerializer(serializers.Serializer):
        code = serializers.ReadOnlyField(default=error_code)
        detail = serializers.ReadOnlyField(default=error_description)
        data = additional_data(many=additional_data_many)

        class Meta:
            ref_name = reference_name + str(error_code)

    return ErrorResponseSerializer


def error_detail(
        error_code: int,
        error_description: str,
        data: Optional[Union[dict, Iterable]] = None,
) -> dict:
    detail = {
        "code": error_code,
        "detail": error_description,
    }

    if data is not None:
        detail.update({"data": data})
    return detail
