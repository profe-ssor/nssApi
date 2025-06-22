# file_uploads/serializers.py
from rest_framework import serializers
from .models import UploadPDF

class UploadPDFSerializer(serializers.ModelSerializer):
    is_evaluation_form = serializers.ReadOnlyField()
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()

    class Meta:
        model = UploadPDF
        fields = [
            'id', 'file_name', 'file', 'signature_image',
            'signature_drawing', 'is_signed', 'signed_file', 
            'uploaded_at', 'form_type', 'priority',
            'receiver', 'is_evaluation_form',
            'sender_name', 'receiver_name'
        ]
        read_only_fields = [
            'id', 'is_signed', 'signed_file', 'uploaded_at',
            'signature_drawing', 'signature_image'
        ]

    def get_sender_name(self, obj):
        return obj.user.get_full_name() if obj.user else None

    def get_receiver_name(self, obj):
        return obj.receiver.get_full_name() if obj.receiver else None
