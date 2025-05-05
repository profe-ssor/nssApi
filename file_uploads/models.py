from django.db import models

from digital360Api.models import MyUser

# Create your models here.

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