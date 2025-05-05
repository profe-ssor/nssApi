from django.urls import path
from . import views

urlpatterns = [
    path('adminsdb/', views.AdministratorsDatabase, name='admindb'),
    path('getAlladmins/', views.get_all_AdministratorsDataBase, name='alladmins'),
    path('countadmins/', views.count_AdministratorsDataBase, name='countadmins'),
]
