from django.db import models
from django.conf import settings
from django.utils import timezone

class Evaluation(models.Model):
    TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('project', 'Project'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='evaluations/', null=True, blank=True)

    signed_pdf = models.FileField(upload_to='signed_evaluations/', blank=True, null=True)
    
    # Classification
    evaluation_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Users - Custom User model (MyUser)
    nss_personnel = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_evaluations',
        limit_choices_to={'user_type': 'nss'}
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_evaluations',
        limit_choices_to={'user_type': 'supervisor'}
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField()
    
    # Comments
    supervisor_comments = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now() and self.status in ['pending', 'under_review']
    
    @property
    def completed_today(self):
        today = timezone.now().date()
        return (self.status in ['approved', 'rejected'] and 
                self.reviewed_at and self.reviewed_at.date() == today)
