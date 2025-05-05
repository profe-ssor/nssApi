from django.db import models

from digital360Api.models import MyUser
from nss_supervisors.models import Supervisor

# Create your models here.

class Administrator(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name="administrator_profile")
    full_name = models.CharField(max_length=255)
    ghana_card_record = models.CharField(max_length=20)
    contact = models.CharField(max_length=20)
    assigned_supervisors = models.ManyToManyField(Supervisor, related_name='managed_by_admin')

    def __str__(self):
        return f"Administrator: {self.full_name }"
    