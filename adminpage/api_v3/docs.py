import re
from inspect import cleandoc
from types import ModuleType

from fastapi.routing import APIRoute

# API version
VERSION = "v3"

# Info for OpenAPI specification
TITLE = "InnoSport"
SUMMARY = "InnoSport platform at Innopolis University."

DESCRIPTION = """
### About this project

This is the API for InnoSport platform at Innopolis University.

Students check in for sport classes, instructors manage the schedule and collect attendance.

Useful links:
- [InnoSport source code](https://github.com/one-zero-eight/sport)
- [InnoSport Website](https://sport.innopolis.university/)
"""

CONTACT_INFO = {
    "name": "one-zero-eight (Telegram)",
    "url": "https://t.me/one_zero_eight",
}

LICENSE_INFO = {
    "name": "MIT License",
    "identifier": "MIT",
}


def safe_cleandoc(doc: str | None) -> str:
    return cleandoc(doc) if doc else ""


def doc_from_module(module: ModuleType) -> str:
    return safe_cleandoc(module.__doc__)


TAGS_INFO = []


def generate_unique_operation_id(route: APIRoute) -> str:
    # Better names for operationId in OpenAPI schema.
    # It is needed because clients generate code based on these names.
    # Requires pair (tag name + function name) to be unique.
    # See fastapi.utils:generate_unique_id (default implementation).
    if route.tags:
        operation_id = f"{route.tags[0]}_{route.name}".lower()
    else:
        operation_id = route.name.lower()
    operation_id = re.sub(r"\W+", "_", operation_id)
    return operation_id
