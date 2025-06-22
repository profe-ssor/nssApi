# messages/serializers.py
from rest_framework import serializers
from digital360Api.models import MyUser
from file_uploads.serializers import UploadPDFSerializer
from .models import Message, UserConnection
from .utils import get_user_full_name

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    attachment_details = UploadPDFSerializer(source='attachment', read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(read_only=True)
    reply_to_content = serializers.SerializerMethodField()
    forwarded_from = serializers.PrimaryKeyRelatedField(read_only=True)
    forwarded_from_details = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    is_today = serializers.ReadOnlyField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'receiver', 'sender_name', 'receiver_name','sender_role','subject',
            'content', 'attachment', 'attachment_details', 'timestamp', 'is_read',
            'reply_to', 'reply_to_content', 'forwarded_from', 'forwarded_from_details',
            'is_forwarded', 'priority', 'priority_display',
            'message_type', 'type_display', 'is_today'
        ]
        read_only_fields = ['id', 'timestamp', 'is_read', 'sender_name', 'receiver_name', 'is_today', 'is_forwarded']

    def get_sender_name(self, obj):
        return get_user_full_name(obj.sender)

    def get_receiver_name(self, obj):
        return get_user_full_name(obj.receiver)
    
    def get_sender_role(self, obj):  # 👈 This will return actual sender role
        return getattr(obj.sender, 'user_type', 'unknown')


    def get_reply_to_content(self, obj):
        if obj.reply_to:
            return obj.reply_to.content
        return None

    def get_forwarded_from_details(self, obj):
        if obj.forwarded_from:
            return {
                'id': obj.forwarded_from.id,
                'content': obj.forwarded_from.content,
                'original_sender': get_user_full_name(obj.forwarded_from.sender),
                'timestamp': obj.forwarded_from.timestamp
            }
        return None

class UserConnectionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    can_message_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserConnection
        fields = ['id', 'user', 'can_message', 'user_name', 'can_message_name', 'connection_type', 'created_at']
        read_only_fields = ['id', 'created_at', 'user_name', 'can_message_name']
    
    def get_user_name(self, obj):
        return get_user_full_name(obj.user)
    
    def get_can_message_name(self, obj):
        return get_user_full_name(obj.can_message)

class MessageStatsSerializer(serializers.Serializer):
    """Serializer for message statistics"""
    total_messages = serializers.IntegerField()
    unread_messages = serializers.IntegerField()
    today_messages = serializers.IntegerField()
    high_priority = serializers.IntegerField()
    medium_priority = serializers.IntegerField()
    low_priority = serializers.IntegerField()
    inquiry_count = serializers.IntegerField()
    feedback_count = serializers.IntegerField()
    report_count = serializers.IntegerField()
    
class UserDropdownSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = ['id', 'full_name', 'user_type']

    def get_full_name(self, obj):
        return get_user_full_name(obj)  # ✅ use the utility function

