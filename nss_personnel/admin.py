from .models import NSSPersonnel, ArchivedNSSPersonnel
from django.contrib import admin

# Register your models here.

class ArchivedNSSPersonnelAdmin(admin.ModelAdmin):
    list_display = ("ghana_card_record", "nss_id", "full_name", "batch_year", "completion_date", "archived_at")
    search_fields = ("ghana_card_record", "nss_id", "full_name", "batch_year")
    actions = ["restore_personnel"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def restore_personnel(self, request, queryset):
        # Placeholder for restore logic
        self.message_user(request, "Restore action not yet implemented.")
    restore_personnel.short_description = "Restore selected personnel to active"

admin.site.register(ArchivedNSSPersonnel, ArchivedNSSPersonnelAdmin)
