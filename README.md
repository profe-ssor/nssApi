source venv/bin/activate
venv\Scripts\activate
cd nssApi

//Install dependencies//
pip install -r requirements.txt

//Apply database migrations//
py manage.py makemigrations
py manage.py migrate

//Create a superuser (admin account)//
py manage.py createsuperuser

//Run the development server//
python manage.py runserver
