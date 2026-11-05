@echo off
REM First-time setup for the website. Run from the website\ folder.
python -m venv venv
call venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py makemigrations pages
python manage.py migrate
python manage.py seed_site
echo.
echo Now create your admin login:
python manage.py createsuperuser
echo.
echo All set. Start the site with:  venv\Scripts\activate  then  python manage.py runserver
echo Then open http://127.0.0.1:8000/  (admin: http://127.0.0.1:8000/admin/)
