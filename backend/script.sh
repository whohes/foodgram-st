#!/bin/sh

echo 'Running migrations...'
python manage.py makemigrations users
python manage.py makemigrations recipes
python manage.py makemigrations urlshortner
python manage.py migrate

echo 'Collecting static files...'
python manage.py collectstatic --no-input 
sh -c "cp -r /app/collected_static/ /backend_static/static/"

echo 'Loading ingredients...'
python manage.py load_ingredients

echo 'Starting server...'
gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi
exec "$@"