from django.contrib import admin
from .models import MyUser, Region, OTPVerification, UploadPDF


admin.site.register(MyUser)
admin.site.register(Region)
admin.site.register(OTPVerification)
admin.site.register(UploadPDF)
