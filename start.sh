#!/bin/bash
# Wait for Postgres
echo "Waiting for Postgres..."
while ! nc -z $PG_HOST $PG_PORT; do
  sleep 1
done
echo "Postgres is up!"

# Run Django migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Compress CSS/JS
python manage.py compress

# Start Gunicorn
gunicorn bhushan_web.wsgi:application \
--bind 0.0.0.0:8000 \
    --workers 4 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
