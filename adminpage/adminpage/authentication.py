import json
from datetime import datetime, timedelta
from typing import List

import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import get_authorization_header, BaseAuthentication

from accounts.models import User as _User_type

User: _User_type = get_user_model()


class InNoHassleAuthentication(BaseAuthentication):
    """
    Custom authentication class for InNoHassle Accounts.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """

        auth = get_authorization_header(request).split()

        # Check Bearer
        if not auth or auth[0].lower() != "bearer".encode():
            return None

        if len(auth) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string contains spaces.')

        try:
            token = auth[1].decode()
        except UnicodeError:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string contains invalid characters.')

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token: str):
        """
        Validate the token and return a user matching email.
        """

        claims = InNoHassleAccounts.decode_jwt(token)
        if not claims:
            # Invalid token. Let other authentication classes handle it.
            return None

        try:
            user = User.objects.get(**{
                User.USERNAME_FIELD: claims[innohassle_settings['USERNAME_CLAIM']]
            })
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        return user, token

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """

        return "Bearer"


class InNoHassleAccounts:
    keys: List[RSAPublicKey] = []
    keys_timestamp: datetime = datetime.min

    @classmethod
    def decode_jwt(cls, token: str):
        """
        Decode the JWT token and return the payload.
        """

        # Fetch the keys if necessary
        cls.load_keys()

        # Decode the token using each key
        for key in cls.keys:
            try:
                return jwt.decode(
                    token,
                    key=key,
                    algorithms=['RS256', 'RS384', 'RS512'],
                    audience=innohassle_settings['AUDIENCE'],
                    # Explicitly define options to protect
                    # against changes in the library
                    verify=True,
                    options={
                        'verify_signature': True,
                        'verify_exp': True,
                        'verify_nbf': True,
                        'verify_iat': True,
                        'verify_aud': True,
                        'verify_iss': False,
                        'require_exp': False,
                        'require_iat': False,
                        'require_nbf': False,
                    },
                )
            except jwt.ExpiredSignatureError:
                raise exceptions.AuthenticationFailed('Token expired')
            except jwt.PyJWTError:
                continue
        return None

    @classmethod
    def load_keys(cls):
        """
        Check if the keys need to be refreshed and load them if necessary.
        """

        refresh_time = datetime.now() - timedelta(hours=innohassle_settings["KEYS_RELOAD_INTERVAL"])
        if cls.keys_timestamp < refresh_time:
            # Load the keys and update the timestamp
            success = cls._load_keys()
            if success:
                cls.keys_timestamp = datetime.now()

    @classmethod
    def _load_keys(cls):
        jwks_uri = f"{innohassle_settings['API_URL']}/.well-known/jwks.json"

        # Fetch the JWKS
        try:
            response = requests.get(jwks_uri)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException:
            return False

        # Load the keys
        keys = []
        for key in result["keys"]:
            try:
                keys.append(RSAAlgorithm.from_jwk(json.dumps(key)))
            except jwt.PyJWTError:
                continue

        if len(keys) == 0 and len(cls.keys) > 0:
            # Something went wrong
            return False

        # Success
        cls.keys = keys
        return True


innohassle_settings = settings.AUTH_INNOHASSLE
