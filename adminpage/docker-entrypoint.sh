#!/bin/sh

set -e

# Activate our virtual environment here
. /opt/pysetup/.venv/bin/activate

# Ensure migrations are applied and static files are collected
if [ -z "$NO_MIGRATE" ]; then
    python3 manage.py collectstatic --noinput
    python3 manage.py migrate
    python3 manage.py createcachetable
fi

# Evaluating passed command:
exec "$@"
