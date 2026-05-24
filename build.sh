#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', '')
last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', '')
if username and password and not User.objects.filter(username=username).exists():
    u = User.objects.create_superuser(username=username, email=email, password=password)
    u.role = 'Admin'
    u.first_name = first_name
    u.last_name = last_name
    u.save()
    print('Superuser created with Admin role.')
else:
    print('Superuser already exists or credentials not set.')
"
