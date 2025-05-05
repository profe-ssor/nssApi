from rest_framework import serializers

from file_uploads.serializers import UploadPDFSerializer
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.get_full_name', read_only=True)
    attachment_details = UploadPDFSerializer(source='attachment', read_only=True)  # Add this
    

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'receiver', 'sender_name', 'receiver_name',
            'content', 'attachment', 'attachment_details','timestamp', 'is_read'
        ]
        read_only_fields = ['id', 'timestamp', 'is_read', 'sender_name', 'receiver_name']
