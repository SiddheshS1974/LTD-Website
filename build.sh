#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
from api.models import ValidHGICode
if not ValidHGICode.objects.exists():
    from django.core.management import call_command
    call_command('loaddata', 'api/fixtures/hgi_codes.json')
    print('HGI codes loaded from fixture.')
else:
    print('HGI codes already exist — skipping.')
"
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', '')
last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', '')
if username and password:
    if not User.objects.filter(username=username).exists():
        u = User.objects.create_superuser(username=username, email=email, password=password)
        u.role = 'Admin'
        u.first_name = first_name
        u.last_name = last_name
        u.hgi_code = os.environ.get('DJANGO_SUPERUSER_HGI_CODE', '') or None
        u.save()
        print('Superuser created with Admin role.')
    else:
        u = User.objects.get(username=username)
        changed = False
        if u.role != 'Admin':
            u.role = 'Admin'
            changed = True
        if first_name and not u.first_name:
            u.first_name = first_name
            changed = True
        if last_name and not u.last_name:
            u.last_name = last_name
            changed = True
        hgi_code = os.environ.get('DJANGO_SUPERUSER_HGI_CODE', '')
        if hgi_code and not u.hgi_code:
            u.hgi_code = hgi_code
            changed = True
        if changed:
            u.save()
            print('Existing superuser updated.')
        else:
            print('Superuser already exists and is up to date.')
else:
    print('Superuser credentials not set — skipping.')
"
