from drf_spectacular.extensions import OpenApiAuthenticationExtension, OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes


class InNoHassleAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'adminpage.authentication.InNoHassleAuthentication'
    name = 'innohassle_token'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'description': 'InNoHassle Accounts authentication. Get your token from https://api.innohassle.ru/accounts/v0/tokens/generate-my-sport-token',
        }


class CategoryFieldFix(OpenApiSerializerFieldExtension):
    target_class = 'rest_framework.serializers.ReadOnlyField'

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)
