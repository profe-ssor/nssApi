from django.db import models

from digital360Api.models import MyUser, Region, Workplace

# Create your models here.
# ===============================
# Supervisor Model
# ===============================
class Supervisor(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name="supervisor_profile")
    full_name = models.CharField(max_length=255)
    ghana_card_record = models.CharField(max_length=20) 
    contact = models.CharField(max_length=20)
    assigned_region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)
    assigned_workplace = models.ForeignKey(Workplace, on_delete=models.SET_NULL, null=True, related_name='supervisors')  # ✅ Changed to ForeignKey  # Changed to ManyToManyField
   

    def get_full_name(self):
         return self.full_name
  
    
    def __str__(self):
           return f"{self.full_name} ({self.ghana_card_record})"

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('submission', 'Submission'),
        ('approval', 'Approval'),
        ('message', 'Message'),
        ('personnel', 'Personnel'),
    ]
    supervisor = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    personnel = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ['-timestamp']