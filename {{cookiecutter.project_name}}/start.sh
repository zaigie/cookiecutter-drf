#!/bin/sh

set -a
source .env
set +a

python manage.py collectstatic --noinput
python manage.py migrate

uwsgi --ini /app/uwsgi.ini
