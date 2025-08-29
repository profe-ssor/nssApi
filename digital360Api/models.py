from django.utils import timezone
import secrets
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser

# ===============================
# Custom User Model (MyUser)
# ===============================
class MyUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('nss', 'NSS Personnel'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrator'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='myuser_set',
        blank=True,
        )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='myuser_permissions_set',
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        """ Automatically set is_superuser and is_staff based on user_type """
        if self.user_type == 'admin':
            self.is_superuser = True
            self.is_staff = True
        elif self.user_type == 'supervisor':
            self.is_superuser = False
            self.is_staff = True
        else:  # 'nss'
            self.is_superuser = False
            self.is_staff = False
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.user_type})"


# ===============================
# Region Model
# ===============================
class Region(models.Model):
    GHANA_REGIONS = [
        ('Greater Accra', 'Greater Accra'),
        ('Western', 'Western'),
        ('Ashanti', 'Ashanti'),
        ('Eastern', 'Eastern'),
        ('Central', 'Central'),
        ('Volta', 'Volta'),
        ('Northern', 'Northern'),
        ('Western North', 'Western North'),
        ('Oti', 'Oti'),
        ('Ahafo', 'Ahafo'),
        ('Bono', 'Bono'),
        ('Bono East', 'Bono East'),
        ('Upper East', 'Upper East'),
        ('Upper West', 'Upper West'),
        ('North East', 'North East'),
    ]
    name = models.CharField(max_length=255, choices=GHANA_REGIONS)

    def __str__(self):
        return self.name

# ===============================
# Ghana Card Record Model
# ===============================
class GhanaCardRecord(models.Model):
    ghana_card_number = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=100, default="Ghanaian")
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    address = models.TextField()

    def __str__(self):
        return f"{self.full_name} ({self.ghana_card_number})"
    
# ===============================
# University Record Model
# ===============================
class UniversityRecord(models.Model):
    full_name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=20, unique=True, default="DEFAULT_ID")
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    ghana_card_number = models.ForeignKey(GhanaCardRecord, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    university_name = models.CharField(max_length=255)
    course = models.CharField(max_length=255)
    enrollment_year = models.CharField(max_length=255)
    graduation_year = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.full_name} - {self.university_name} ({self.enrollment_year}-{self.graduation_year})"


# ===============================
# Workplace Model
# ===============================
class Workplace(models.Model):
    workplace_name = models.CharField(max_length=255)
    location_address = models.TextField()
    geolocation_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    geolocation_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    def __str__(self):
        return self.workplace_name


    
class OTPVerification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6, default=secrets.token_hex(3))
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return str(self.user)


# ===============================
# Ghost Detection Model
# ===============================
class GhostDetection(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Admin Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
        ('disciplinary_action', 'Disciplinary Action Taken'),
    ]
    
    nss_personnel = models.ForeignKey('nss_personnel.NSSPersonnel', on_delete=models.CASCADE)
    supervisor = models.ForeignKey('nss_supervisors.Supervisor', on_delete=models.CASCADE)
    assigned_admin = models.ForeignKey('nss_admin.Administrator', on_delete=models.CASCADE, null=True, blank=True)
    detection_flags = models.JSONField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submission_attempt = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    admin_action_taken = models.TextField(blank=True)
    evaluation_form_id = models.IntegerField(null=True, blank=True, help_text="ID of the evaluation form that triggered this detection")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Ghost Detection: {self.nss_personnel.full_name} - {self.severity}"
    

class OutgoingNSSPersonnel(models.Model):
    """
    Database to store outgoing NSS personnel who have completed their service.
    This prevents duplicate Ghana Card submissions for new batches.
    """
    ghana_card_id = models.CharField(max_length=100, unique=True, help_text="Ghana Card ID to prevent duplicates")
    nss_id = models.CharField(max_length=25, help_text="Original NSS ID")
    full_name = models.CharField(max_length=255, help_text="Full name of personnel")
    service_start_date = models.CharField(max_length=10, help_text="When service started")
    service_end_date = models.CharField(max_length=10, help_text="When service ended")
    region_served = models.CharField(max_length=100, help_text="Region where they served")
    department = models.CharField(max_length=50, help_text="Department they worked in")
    institution_assigned = models.CharField(max_length=255, help_text="Institution they were assigned to")
    supervisor_name = models.CharField(max_length=255, blank=True, null=True, help_text="Supervisor during service")
    performance_rating = models.CharField(max_length=30, blank=True, null=True, help_text="Final performance rating")
    completion_year = models.IntegerField(help_text="Year when service was completed")
    transfer_date = models.DateTimeField(auto_now_add=True, help_text="When transferred to outgoing database")
    transfer_reason = models.CharField(max_length=50, default='evaluation_submitted', help_text="Reason for transfer")
    
    class Meta:
        verbose_name = "Outgoing NSS Personnel"
        verbose_name_plural = "Outgoing NSS Personnel"
        ordering = ['-transfer_date']
    
    def __str__(self):
        return f"{self.full_name} ({self.ghana_card_id}) - Completed {self.completion_year}"
    
    @classmethod
    def is_ghana_card_used(cls, ghana_card_id):
        """Check if a Ghana Card ID has been used by any outgoing personnel"""
        return cls.objects.filter(ghana_card_id=ghana_card_id).exists()
    
    @classmethod
    def transfer_personnel(cls, nss_personnel, transfer_reason='evaluation_submitted'):
        """Transfer an NSS personnel to the outgoing database"""
        from datetime import datetime
        
        # Create outgoing personnel record
        outgoing = cls.objects.create(
            ghana_card_id=nss_personnel.ghana_card_record,
            nss_id=nss_personnel.nss_id,
            full_name=nss_personnel.full_name,
            service_start_date=nss_personnel.start_date,
            service_end_date=nss_personnel.end_date,
            region_served=str(nss_personnel.region_of_posting),
            department=nss_personnel.department,
            institution_assigned=nss_personnel.assigned_institution,
            supervisor_name=nss_personnel.assigned_supervisor.full_name if nss_personnel.assigned_supervisor else None,
            performance_rating=nss_personnel.performance,
            completion_year=datetime.now().year,
            transfer_reason=transfer_reason
        )
        
        # Delete from active NSS personnel
        nss_personnel.delete()
        
        return outgoing
    
