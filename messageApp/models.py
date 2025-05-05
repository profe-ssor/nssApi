# messages/models.py
from django.db import models
from django.conf import settings
from file_uploads.models import UploadPDF  # Add this import

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages'
    )
    content = models.TextField(blank=True)
    # Change from FileField to ForeignKey
    attachment = models.ForeignKey(
        UploadPDF, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.email} to {self.receiver.email} at {self.timestamp}"

