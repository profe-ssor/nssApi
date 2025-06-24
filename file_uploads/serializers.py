from rest_framework import serializers
from .models import UploadPDF
from messageApp.utils import get_user_full_name

class UploadPDFSerializer(serializers.ModelSerializer):
    is_evaluation_form = serializers.ReadOnlyField()
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()
    mark_as_signed = serializers.BooleanField(write_only=True, required=False)
    status = serializers.ChoiceField(choices=UploadPDF.STATUS_CHOICES, required=False)
    

    class Meta:
        model = UploadPDF
        fields = [
            'id', 'file_name', 'file',
            'signature_image', 'signature_drawing',
            'is_signed', 'signed_file',
            'uploaded_at', 'form_type', 'priority',
            'receiver', 'is_evaluation_form',
            'sender_name', 'receiver_name',
            'mark_as_signed',  'submitted_date', 'due_date', 'status',
        ]
        read_only_fields = [
            'id', 'is_signed', 'signed_file', 'uploaded_at',
            'signature_drawing', 'signature_image', 'submitted_date', 'due_date'
        ]

    def get_sender_name(self, obj):
        return get_user_full_name(obj.user) if obj.user else None

    def get_receiver_name(self, obj):
        return get_user_full_name(obj.receiver) if obj.receiver else None

    def create(self, validated_data):
        mark_as_signed = validated_data.pop('mark_as_signed', False)
        pdf_instance = super().create(validated_data)

        if mark_as_signed:
            pdf_instance.is_signed = True
            pdf_instance.signed_file = pdf_instance.file  # Use original file
            pdf_instance.save()

        return pdf_instance

    def update(self, instance, validated_data):
        mark_as_signed = validated_data.pop('mark_as_signed', False)
        instance = super().update(instance, validated_data)

        if mark_as_signed and not instance.is_signed:
            instance.is_signed = True
            instance.signed_file = instance.file  # Use original file
            instance.save()

        return instance
