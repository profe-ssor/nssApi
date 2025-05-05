from django.urls import path
from . import views

urlpatterns = [
    path('pdf/upload/', views.upload_pdf, name='upload_pdf'),
    path('pdf/list/', views.list_pdfs, name='list_pdfs'),
    path('pdf/<int:pk>/', views.get_pdf, name='get_pdf'),
    path('pdf/sign/image/<int:pk>/', views.sign_with_image, name='sign_with_image'),
    # path('pdf/sign/draw/<int:pk>/', views.sign_with_drawing, name='sign_with_drawing'),

    path('signed/', views.list_signed_pdfs, name='list_signed_pdfs'),
    path('signed/all/', views.list_all_signed_pdfs, name='list_all_signed_pdfs'),
    path('signed/<int:pk>/', views.get_signed_pdf, name='get_signed_pdf'),
]
