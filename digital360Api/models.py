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
    ghana_card_number = models.CharField(max_length=20, unique=True)
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
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Ghost Detection: {self.nss_personnel.full_name} - {self.severity}"
    
