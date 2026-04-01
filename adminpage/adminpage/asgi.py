import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adminpage.settings')

from django.core.asgi import get_asgi_application

# Initialize Django (should be before any other imports)
django_asgi_app = get_asgi_application()

# Initialize FastAPI
from api_v3.app import app as fastapi_asgi_app


async def application(scope, receive, send):
    if scope["type"] == "http":
        # Route requests to either FastAPI or Django based on the path
        if scope["path"].startswith("/api/v3"):
            await fastapi_asgi_app(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)
    elif scope["type"] == "lifespan":
        # Django ASGIHandler does not support lifespan events, so pass request only to FastAPI.
        await fastapi_asgi_app(scope, receive, send)
    elif scope["type"] == "websocket":
        # Django ASGIHandler does not support WebSockets, so pass request only to FastAPI.
        await fastapi_asgi_app(scope, receive, send)
