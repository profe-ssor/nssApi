from calendar import monthrange
from datetime import datetime, timezone
from django.db import models
from digital360Api.models import MyUser

class UploadPDF(models.Model):
    FORM_TYPE_CHOICES = [
        ('Monthly', 'Monthly Evaluation'),
        ('Quarterly', 'Quarterly Evaluation'), 
        ('Annual', 'Annual Evaluation'),
        ('Project', 'Project Evaluation'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True)
    receiver = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_evaluations')
    
    submitted_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    file_name = models.CharField(max_length=255, default="Untitled")
    file = models.FileField(upload_to='documents/')
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature_drawing = models.TextField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    signed_file = models.FileField(upload_to='signed_docs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, default='Monthly')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at}"
    
    @property
    def is_evaluation_form(self):
        return self.form_type in ['Monthly', 'Quarterly', 'Annual', 'Project']
    
    def calculate_due_date(self):
        now = timezone.now()
        year, month = now.year, now.month
        last_day = monthrange(year, month)[1]
        due_day = last_day - 20  # last 3 weeks ≈ 21 days, start on 10th
        return timezone.make_aware(datetime(year, month, due_day, 23, 59, 59))

