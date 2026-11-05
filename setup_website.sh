#!/usr/bin/env bash
# First-time setup for the website (Mac/Linux). Run from the website/ folder.
set -e
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python manage.py makemigrations pages
python manage.py migrate
python manage.py seed_site
echo "Now create your admin login:"
python manage.py createsuperuser
echo "All set. Start the site with:  source venv/bin/activate && python manage.py runserver"
