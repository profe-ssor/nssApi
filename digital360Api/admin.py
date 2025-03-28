from django.contrib import admin
from .models import MyUser, Region, OTPVerification, UploadPDF, GhanaCardRecord, UniversityRecord, NSSPersonnel,Workplace,Administrator , Supervisor


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