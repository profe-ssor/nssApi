from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('admin/dashboard/stats/', views.admin_dashboard_stats, name='admin-dashboard-stats'),
    path('personnel-submissions/', views.personnel_submissions, name='personnel-submissions'),
    
    # Evaluation management
    path('supervisor/evaluations/', views.supervisor_evaluation_list, name='supervisor-evaluations'),
    path('admin/evaluations/', views.admin_evaluations_list, name='admin-evaluations'),
    path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation-detail'),
    path('evaluations/<int:pk>/update-status/', views.evaluation_status_update, name='evaluation-status-update'),
    path('admin/evaluations/<int:pk>/update-status/', views.admin_evaluation_status_update, name='admin-evaluation-status-update'),
    
    # Bulk actions
    path('evaluations/bulk-update/', views.bulk_status_update, name='bulk-status-update'),
    path('admin/activity/', views.admin_activity_logs, name='admin-activity-logs'),
    path('personnel/evaluations/', views.personnel_evaluation_list, name='personnel-evaluations'),
]
