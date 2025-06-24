from django.contrib import admin

# Register your models here.
# file_uploads/admin.py
from django.contrib import admin
from .models import UploadPDF

admin.site.register(UploadPDF)
