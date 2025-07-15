from django.urls import path
from . import views

urlpatterns = [
    path('adminsdb/', views.AdministratorsDatabase, name='admindb'),
    path('getAlladmins/', views.get_all_AdministratorsDataBase, name='alladmins'),
    path('countadmins/', views.count_AdministratorsDataBase, name='countadmins'),
    path('adminsdb/<int:admin_id>/', views.get_or_update_admin_by_id, name='get_or_update_admin_by_id'),
    path('adminsdb/by_user/<int:user_id>/', views.get_admin_by_user_id, name='get_admin_by_user_id'),
]
