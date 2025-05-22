from rest_framework import serializers
from file_uploads.serializers import UploadPDFSerializer
from .models import Message
from .utils import get_user_full_name

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()
    attachment_details = UploadPDFSerializer(source='attachment', read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(read_only=True)
    reply_to_content = serializers.SerializerMethodField()  # ✅ new field

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'receiver', 'sender_name', 'receiver_name',
            'content', 'attachment', 'attachment_details', 'timestamp', 'is_read',
            'reply_to', 'reply_to_content'  # ✅ include new field
        ]
        read_only_fields = ['id', 'timestamp', 'is_read', 'sender_name', 'receiver_name']

    def get_sender_name(self, obj):
        return get_user_full_name(obj.sender)

    def get_receiver_name(self, obj):
        return get_user_full_name(obj.receiver)

    def get_reply_to_content(self, obj):
        if obj.reply_to:
            return obj.reply_to.content
        return None
