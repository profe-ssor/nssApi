from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView


urlpatterns = [
    path('', views.index, name='setup'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('supervisor-dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('logout/', views.logout, name='logout'),
    path('regions/', views.regions, name='regions'),
]
