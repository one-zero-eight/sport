from typing import Annotated

import rest_framework.exceptions
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from accounts.models import User
from adminpage.authentication import innohassle_settings, InNoHassleAccounts
from api_v3.exceptions import IncorrectCredentialsException

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Sport Token from [InNoHassle Accounts](https://api.innohassle.ru/accounts/v0/tokens/generate-my-sport-token)",
    bearerFormat="JWT",
    auto_error=False,  # We'll handle error manually
)


async def verify_user(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    token = bearer and bearer.credentials
    if not token:
        raise IncorrectCredentialsException(no_credentials=True)

    try:
        claims = InNoHassleAccounts.decode_jwt(token)
    except rest_framework.exceptions.AuthenticationFailed:  # Token expired
        raise IncorrectCredentialsException(no_credentials=False)

    if not claims:  # Invalid token
        raise IncorrectCredentialsException(no_credentials=False)

    try:
        user = await User.objects.prefetch_related("student", "student__student_status", "trainer").aget(**{
            User.USERNAME_FIELD: claims[innohassle_settings['USERNAME_CLAIM']]
        })
        return user
    except User.DoesNotExist:
        raise IncorrectCredentialsException(no_credentials=False)


VerifiedDep = Annotated[User, Depends(verify_user)]
