import secrets
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


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


class MyUser(AbstractUser):
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    nss_id = models.CharField(max_length=50, unique=True)
    ghana_card = models.CharField(max_length=50, unique=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    date_of_birth = models.CharField(max_length=10)
    assigned_institution = models.CharField(max_length=255)
    start_date = models.CharField(max_length=10)
    end_date = models.CharField(max_length=10)
    phone = models.CharField(max_length=10)
    region_of_posting = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='posted_users'
    )
    resident_address = models.CharField(max_length=255)

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
    REQUIRED_FIELDS = [
        'username', 'nss_id', 'ghana_card', 'gender', 'date_of_birth',
        'assigned_institution', 'start_date', 'end_date', 'phone',
        'region_of_posting', 'resident_address'
    ]

class OTPVerification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6, default=secrets.token_hex(3))
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return self.user.username
    

# models.py
class UploadPDF(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True)
    file_name = models.CharField(max_length=255, default="Untitled")
    file = models.FileField(upload_to='documents/')
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature_drawing = models.TextField(null=True, blank=True)  # Stores base64 drawing data
    is_signed = models.BooleanField(default=False)
    signed_file = models.FileField(upload_to='signed_docs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at}"