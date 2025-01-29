#!/bin/sh

set -e

# Activate our virtual environment here
. /opt/pysetup/.venv/bin/activate

# You can put other setup logic here
python3 manage.py collectstatic --noinput
python3 manage.py migrate
python3 manage.py createcachetable

# Evaluating passed command:
exec "$@"
