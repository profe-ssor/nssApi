from django.db import models
from digital360Api.models import MyUser

class UploadPDF(models.Model):
    FORM_TYPE_CHOICES = [
        ('Monthly', 'Monthly Evaluation'),
        ('Quarterly', 'Quarterly Evaluation'), 
        ('Annual', 'Annual Evaluation'),
        ('Project', 'Project Evaluation'),
        ('General', 'General Document'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True)
    file_name = models.CharField(max_length=255, default="Untitled")
    file = models.FileField(upload_to='documents/')
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature_drawing = models.TextField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    signed_file = models.FileField(upload_to='signed_docs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Add form type for evaluation integration
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, default='General')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at}"
    # file_uploads/models.py
from django.db import models
from digital360Api.models import MyUser

class UploadPDF(models.Model):
    FORM_TYPE_CHOICES = [
        ('Monthly', 'Monthly Evaluation'),
        ('Quarterly', 'Quarterly Evaluation'), 
        ('Annual', 'Annual Evaluation'),
        ('Project', 'Project Evaluation'),
        ('General', 'General Document'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True)
    receiver = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_evaluations')
    
    file_name = models.CharField(max_length=255, default="Untitled")
    file = models.FileField(upload_to='documents/')
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature_drawing = models.TextField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    signed_file = models.FileField(upload_to='signed_docs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, default='General')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at}"
    
    @property
    def is_evaluation_form(self):
        return self.form_type in ['Monthly', 'Quarterly', 'Annual', 'Project']

    @property
    def is_evaluation_form(self):
        return self.form_type in ['Monthly', 'Quarterly', 'Annual', 'Project']