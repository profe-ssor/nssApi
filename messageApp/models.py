# messages/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date
from file_uploads.models import UploadPDF

class Message(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    TYPE_CHOICES = [
        ('inquiry', 'Inquiry'),
        ('feedback', 'Feedback'),
        ('report', 'Report'),
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages'
    )
    subject = models.CharField(max_length=255, blank=True) 
    content = models.TextField(blank=True)
    attachment = models.ForeignKey(
        UploadPDF, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages'
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='inquiry')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    forwarded_from = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='forwarded_messages')
    is_forwarded = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"From {self.sender.email} to {self.receiver.email} - {self.priority} priority"
    
    @property
    def is_today(self):
        return self.timestamp.date() == date.today()

# Add this model to track user connections/relationships
class UserConnection(models.Model):
    """Model to define who can message whom based on organizational hierarchy"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connections_as_user'
    )
    can_message = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connections_as_target'
    )
    connection_type = models.CharField(max_length=50, choices=[
        ('supervisor', 'Supervisor'),
        ('supervisee', 'Supervisee'),
        ('admin', 'Admin'),
        ('peer', 'Peer'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'can_message']
    
    def __str__(self):
        return f"{self.user.email} can message {self.can_message.email} as {self.connection_type}"