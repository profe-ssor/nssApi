from django.db import models
from digital360Api.models import MyUser, Region
from nss_supervisors.models import Supervisor
# Create your models here.
class NSSPersonnel(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name="nss_profile")
    full_name = models.CharField(max_length=255)
    ghana_card_record = models.CharField(max_length=20) 
    nss_id = models.CharField(max_length=25, default='nss_id')
    start_date = models.CharField(max_length=10)
    end_date = models.CharField(max_length=10)
    phone = models.CharField(max_length=10)
    assigned_supervisor = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True, blank=True, related_name='nss_personnel')
    assigned_institution = models.CharField(max_length=255)
    region_of_posting = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='posted_users'
    )
    def get_full_name(self):
         return self.full_name
    
    def __str__(self):
           return f"{self.full_name} ({self.nss_id})"
    