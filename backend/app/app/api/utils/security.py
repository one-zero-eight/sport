import logging

import jwt
from fastapi import HTTPException, Security, Cookie
from fastapi.security.oauth2 import OAuthFlowsModel
from jwt import PyJWTError
from starlette.status import HTTP_403_FORBIDDEN

from app import crud
from app.core import config
from app.core.jwt import ALGORITHM
from app.core.security import CookieAuth
from app.db_models.user import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

reusable_oauth2 = CookieAuth(
    flows=OAuthFlowsModel(
        implicit={
            "authorizationUrl": f"{config.API_BASE_URL}/login"
        }
    ),
    auto_error=False
)


def process_token(token, id_token):
    try:
        # TODO: ask IT dep for verification URL
        access_payload = jwt.decode(token, verify=False, algorithms=[ALGORITHM])
        id_payload = jwt.decode(id_token, verify=False, algorithms=[ALGORITHM])
    except PyJWTError:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return {"access": access_payload, "id": id_payload}


def get_current_user(
        token: str = Security(reusable_oauth2),
        access_token=Cookie(None),  # needs for documentation, anyway cookie token is retrieved by oauth
        id_token=Cookie(...),
):
    if token is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
        )
    return process_token(token, id_token)


def get_current_user_optional(
        token: str = Security(reusable_oauth2),
        access_token=Cookie(None),  # needs for documentation, anyway cookie token is retrieved by oauth
        id_token=Cookie(None),
):
    # TODO Ask IT dep for identification endpoint
    if token is None or id_token is None:
        return None
    return process_token(token, id_token)


def get_current_active_user(current_user: User = Security(get_current_user)):
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(current_user: User = Security(get_current_user)):
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
