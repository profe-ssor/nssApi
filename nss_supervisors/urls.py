from django.urls import path
from . import views
from .views import supervisor_recent_activity

urlpatterns = [
     path('supervisorsdb/', views.SupervisorsDatabase, name='ssdb'), 
    path('getAllsupervisors/', views. get_all_SupervisorsDataBase, name='allsupervisors'),
    path('countsupervisors/', views.count_SupervisorsDataBase, name='countsupervisors'),
    path('recent-activity/', supervisor_recent_activity, name='supervisor_recent_activity'),
    path('update/<int:user_id>/', views.update_supervisor, name='update_supervisor'),
    path('supervisorsdb/<int:user_id>/', views.get_supervisor_by_user_id, name='get_supervisor_by_user_id'),
]
