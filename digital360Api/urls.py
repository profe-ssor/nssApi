from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Test route
    path('register/', views.register, name='register'),  # User registration
    path('logout/', views.logout, name='logout'),  # User logout
    path('login/', views.login, name='login'),  # OTP login
    path('verify-otp/', views.verify_otp, name='verify_otp'),  # OTP verification
    path('resend-otp/', views.resend_otp, name='resend_otp'),  # Resend OTP
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Admin dashboard
    path('supervisor-dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),  # Supervisor dashboard
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),  
    path('regions/', views.regions, name='regions'),  # Get regions
    path('user-counts/', views.user_counts, name='user_counts'), 

    path('pdf/upload/', views.upload_pdf, name='upload_pdf'),
    path('pdf/list/', views.list_pdfs, name='list_pdfs'),
    path('pdf/<int:pk>/', views.get_pdf, name='get_pdf'),
    # path('pdf/sign/image/<int:pk>/', views.sign_with_image, name='sign_with_image'),
    path('pdf/sign/draw/<int:pk>/', views.sign_with_drawing, name='sign_with_drawing'),
# 
]