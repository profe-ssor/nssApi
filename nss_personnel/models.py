from django.db import models
from digital360Api.models import MyUser, Region
from nss_supervisors.models import Supervisor
# Create your models here.
class NSSPersonnel(models.Model):
    
    STATUS_CHOICES = [
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('on_leave', 'On Leave'),
    ('completed', 'Completed'),
]

    PERFORMANCE_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement'),
    ]
    DEPARTMENT_CHOICES = [
        ('education', 'Education'),
        ('health', 'Health'),
        ('agriculture', 'Agriculture'),
        ('finance', 'Finance'),
        ('administration', 'Administration'),
        ('security', 'Security'),
        ('transport', 'Transport'),
        ('works_housing', 'Works and Housing'),
        ('information', 'Information'),
        ('tourism', 'Tourism'),
    ]
    
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name="nss_profile")
    full_name = models.CharField(max_length=255)
    ghana_card_record = models.CharField(max_length=20) 
    nss_id = models.CharField(max_length=25, default='nss_id')
    start_date = models.CharField(max_length=10)
    end_date = models.CharField(max_length=10)
    phone = models.CharField(max_length=10)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    performance = models.CharField(max_length=30, choices=PERFORMANCE_CHOICES, null=True, blank=True)
    assigned_supervisor = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True, blank=True, related_name='nss_personnel')
    assigned_institution = models.CharField(max_length=255)
    department = models.CharField(
        max_length=50, 
        choices=DEPARTMENT_CHOICES, 
        default='education'
    )
    region_of_posting = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='posted_users'
    )
    def get_full_name(self):
         return self.full_name
    
    def __str__(self):
           return f"{self.full_name} ({self.nss_id})"
    

class ArchivedNSSPersonnel(models.Model):
    ghana_card_record = models.CharField(max_length=20, unique=True)
    nss_id = models.CharField(max_length=25)
    full_name = models.CharField(max_length=255)
    batch_year = models.CharField(max_length=10)
    completion_date = models.CharField(max_length=10)
    archived_at = models.DateTimeField(auto_now_add=True)
    restored_once = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} ({self.nss_id}) - Archived"
    