from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser, Region, OTPVerification, GhanaCardRecord, UniversityRecord, Workplace
from nss_admin.models import Administrator
from nss_personnel.models import NSSPersonnel
from nss_supervisors.models import Supervisor
from messageApp.models import Message


class MyUserAdmin(UserAdmin):
    model = MyUser

    list_display = ("email", "username", "gender", "user_type", "is_staff", "is_superuser", "created_at")
    list_filter = ("user_type", "is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("username", "gender", "user_type")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "gender", "user_type", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    search_fields = ("email", "username")
    ordering = ("email",)


# Register models
admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Region)
admin.site.register(OTPVerification)
admin.site.register(UniversityRecord)
admin.site.register(Workplace)
admin.site.register(GhanaCardRecord)
admin.site.register(Supervisor)
admin.site.register(Administrator)
admin.site.register(NSSPersonnel)
admin.site.register(Message)
