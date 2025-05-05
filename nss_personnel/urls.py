from django.urls import path
from . import views

urlpatterns = [
   
    
   
    path('nssdb/', views.NssPersonelDatabase, name='nssdb'),
    path('getAllnssdb/', views.get_all_NssPersonelDataBase, name='allnssdb'),
    path('countnssdb/', views.count_NssPersonelDataBase, name='countnssdb'),


    path('my-supervisor/', views.get_my_supervisor, name='get-my-supervisor'),
    path('my-admin/', views.get_my_admin, name='get-my-admin'),


   

# 
]