#!/bin/sh

echo 'Running migrations...'
# First, create and apply users migrations
python manage.py makemigrations users
python manage.py migrate users

# Then create and apply other migrations
python manage.py makemigrations recipes
python manage.py makemigrations urlshortner
python manage.py migrate

echo 'Collecting static files...'
python manage.py collectstatic --no-input
cp -r /app/static/. /backend_static/static/

echo 'Loading initial data...'
echo '1. Loading ingredients...'
python manage.py load_ingredients

echo '2. Loading users...'
python manage.py load_users

echo '3. Loading recipes...'
python manage.py load_recipes

echo 'Starting server...'
gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi
exec "$@"