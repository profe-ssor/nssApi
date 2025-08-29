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
python3 manage.py customcreatesuperuser

<!-- REgion setup-->
python3 manage.py shell
from digital360Api.models import Region

regions = [
    "Ahafo",
    "Ashanti",
    "Bono",
    "Bono East",
    "Central",
    "Eastern",
    "Greater Accra",
    "North East",
    "Northern",
    "Oti",
    "Savannah",
    "Upper East",
    "Upper West",
    "Volta",
    "Western",
    "Western North",
]

for name in regions:
    Region.objects.get_or_create(name=name)

print("✅ All 16 regions created (or already existed).")


<!-- Solved Admin loged in -->

from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(email="admin@gmail.com")
print(u.username, u.email, u.is_superuser, u.is_active)


from django.contrib.auth import get_user_model
User = get_user_model()

u = User.objects.get(email="kyerematengcollins93@gmail.com")
u.is_superuser = True
u.is_staff = True
u.is_active = True

u.save()



//Run the development server//
python manage.py runserver
