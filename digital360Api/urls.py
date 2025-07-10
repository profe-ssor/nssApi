from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Test route
    path('register/', views.register, name='register'),  # User registration
    path('logout/', views.logout, name='logout'),  # User logout
    path('login/', views.login, name='login'),  # OTP login
    
    path('verify-otp/', views.verify_otp, name='verify_otp'),  # OTP verification
    path('resend-otp/', views.resend_otp, name='resend_otp'),  # Resend OTP

    # Password management
    path('change-password/', views.change_password, name='change_password'),  # Change password
    path('request-password-reset/', views.request_password_reset, name='request_password_reset'),  # Request password reset
    path('confirm-password-reset/', views.confirm_password_reset, name='confirm_password_reset'),  # Confirm password reset

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
    path('workplaces/', views.workplaces, name='workplaces'),  # Get workplaces
    path('user-counts/', views.user_counts, name='user_counts'), 
 
    # Your existing URL patterns
    path('available-supervisors/', views.get_available_supervisors, name='available_supervisors'),
    path('assign-supervisor/<int:nss_id>/', views.assign_supervisor, name='assign_supervisor'),
    path('nss-by-supervisor/<int:supervisor_id>/', views.get_nss_by_supervisor, name='nss_by_supervisor'),
    path('unassigned-nss/', views.get_unassigned_nss, name='unassigned_nss'),
    path('assign-supervisors-to-admin/', views.assign_supervisors_to_admin, name='assign_supervisors_to_admin'),
    path('dashboard/region-data/', views.admin_region_data, name='admin_region_data'),

    # Ghost Detection URLs
    path('ghost-dashboard/', views.admin_ghost_dashboard, name='admin_ghost_dashboard'),
    path('ghost-investigate/<int:detection_id>/', views.admin_investigate_ghost, name='admin_investigate_ghost'),
    path('ghost-resolve/<int:detection_id>/', views.admin_resolve_ghost, name='admin_resolve_ghost'),
    path('test-ghost-detection/', views.test_ghost_detection, name='test_ghost_detection'),
]