web: gunicorn nssApi.wsgi --log-file -
web: python manage.py migrate && gunicorn nssApi.wsgi
