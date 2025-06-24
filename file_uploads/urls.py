from django.urls import path
from . import views

urlpatterns = [
    # Existing PDF operations
    path('pdf/upload/', views.upload_pdf, name='upload_pdf'),
    path('pdf/list/', views.list_pdfs, name='list_pdfs'),
    path('pdf/<int:pk>/', views.get_pdf, name='get_pdf'),
    path('pdf/sign/image/<int:pk>/', views.sign_with_image, name='sign_with_image'),
    path('signed/', views.list_signed_pdfs, name='list_signed_pdfs'),
    path('signed/all/', views.list_all_signed_pdfs, name='list_all_signed_pdfs'),
    path('signed/<int:pk>/', views.get_signed_pdf, name='get_signed_pdf'),

    # Evaluation form specific endpoints
    path('evaluation-form/send/', views.send_evaluation_form, name='upload_evaluation_form'),
    path('evaluation-forms/', views.list_evaluation_forms, name='list_evaluation_forms'),
    path('evaluation-forms/received/', views.received_evaluations, name='received_evaluations'),

    # ✅ Add this new endpoint for updating evaluation status
    path('evaluation-forms/<int:pk>/update-status/', views.update_evaluation_status, name='update_evaluation_status'),
]
