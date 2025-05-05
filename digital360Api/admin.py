from django.contrib import admin

from file_uploads.models import UploadPDF
from nss_admin.models import Administrator
from nss_personnel.models import NSSPersonnel
from nss_supervisors.models import Supervisor
from messageApp.models import  Message
from .models import MyUser, Region, OTPVerification, GhanaCardRecord, UniversityRecord, Workplace


admin.site.register(MyUser)
admin.site.register(Region)
admin.site.register(OTPVerification)
admin.site.register(UploadPDF)
admin.site.register(UniversityRecord)
admin.site.register(Workplace)
admin.site.register(GhanaCardRecord) 
admin.site.register(Supervisor)
admin.site.register(Administrator)
admin.site.register(NSSPersonnel)
admin.site.register(Message)