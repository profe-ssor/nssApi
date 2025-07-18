from django.urls import path
from . import views
from .views import archived_personnel_list, restore_archived_personnel, recent_submissions, check_evaluation_assignments

urlpatterns = [
   
    
   
    path('nssdb/', views.NssPersonelDatabase, name='nssdb'),
    path('getAllnssdb/', views.get_all_NssPersonelDataBase, name='allnssdb'),
    path('countnssdb/', views.count_NssPersonelDataBase, name='countnssdb'),


    path('my-supervisor/', views.get_my_supervisor, name='get-my-supervisor'),
    path('my-admin/', views.get_my_admin, name='get-my-admin'),
    path('my-admins/', views.my_admins, name='my-admins'),


    path('admin/update-nss/<int:nss_id>/', views.admin_update_nss),
    path('supervisor/update-nss/<int:nss_id>/', views.supervisor_update_performance),
    path('counts/status/', views.count_by_status),
    path('counts/performance/', views.count_by_performance),
    
    path('grouped-by-supervisor/', views.grouped_by_supervisor, name='grouped-by-supervisor'),
    path('grouped-by-admin/', views.nss_grouped_by_admin, name='grouped-by-admin'),
    
    path('counts/grouped-by-supervisor/', views.count_nss_by_supervisor, name='count-nss-by-supervisor'),
    path('counts/grouped-by-admin/', views.count_nss_by_admin, name='count-nss-by-admin'),

    path('departments/', views.department_choices, name='department-choices'),

    path('counts/status/supervisor/', views.count_by_status_for_supervisor),
    path('counts/performance/supervisor/', views.count_by_performance_for_supervisor),

    path('assigned-personnel/', views.assigned_personnel_details),

    path('performance_choices/', views.performance_choices, name='performance-choices'),
    path('personnel/<int:pk>/', views.get_personnel_detail),
    path('personnel/by_user/<int:user_id>/', views.get_personnel_by_user),
    path('personnel/<int:pk>/recent-submissions/', recent_submissions),
    path('check-evaluation-assignments/', check_evaluation_assignments),

# 
]
urlpatterns += [
    path('archived/', archived_personnel_list, name='archived-personnel-list'),
    path('archived/restore/<int:pk>/', restore_archived_personnel, name='restore-archived-personnel'),
]