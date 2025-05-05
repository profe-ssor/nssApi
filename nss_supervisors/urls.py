from django.urls import path
from . import views

urlpatterns = [
     path('supervisorsdb/', views.SupervisorsDatabase, name='ssdb'), 
    path('getAllsupervisors/', views. get_all_SupervisorsDataBase, name='allsupervisors'),
    path('countsupervisors/', views.count_SupervisorsDataBase, name='countsupervisors'),

]
