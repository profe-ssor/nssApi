from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    
    # Evaluation management
    path('supervisor/evaluations/', views.supervisor_evaluation_list, name='supervisor-evaluations'),
    path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation-detail'),
    path('evaluations/<int:pk>/update-status/', views.evaluation_status_update, name='evaluation-status-update'),
    
    # Bulk actions
    path('evaluations/bulk-update/', views.bulk_status_update, name='bulk-status-update'),
]
