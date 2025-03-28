from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Test route
    path('register/', views.register, name='register'),  # User registration
    path('logout/', views.logout, name='logout'),  # User logout
    path('login/', views.login, name='login'),  # OTP login
    
    path('verify-otp/', views.verify_otp, name='verify_otp'),  # OTP verification
    path('resend-otp/', views.resend_otp, name='resend_otp'),  # Resend OTP

    path('nssdb/', views.NssPersonelDatabase, name='nssdb'),
    path('getAllnssdb/', views.get_all_NssPersonelDataBase, name='allnssdb'),
    path('countnssdb/', views.count_NssPersonelDataBase, name='countnssdb'),

    path('supervisorsdb/', views.SupervisorsDatabase, name='ssdb'), 
    path('getAllsupervisors/', views. get_all_SupervisorsDataBase, name='allsupervisors'),
    path('countsupervisors/', views.count_SupervisorsDataBase, name='countsupervisors'),

    path('adminsdb/', views.AdministratorsDatabase, name='admindb'),
    path('getAlladmins/', views.get_all_AdministratorsDataBase, name='alladmins'),
    path('countadmins/', views.count_AdministratorsDataBase, name='countadmins'),

    path('ghanacardsdb/', views.ghanaCardRecords, name='ghanacardsdb'),
    path('getAllcards/', views.get_all_GhanaCardRecords, name='gh'),
    path('countghanaCards/', views.count_ghanaCardRecords, name='countghanaCards'),

    path('universitydb/', views.universityDatabase, name='unidb'),
    path('getAlluniversity/', views.get_all_universityDatabase, name='uni'),
    path('countuniversity/', views. count_universityDatabase, name='countuni'),

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