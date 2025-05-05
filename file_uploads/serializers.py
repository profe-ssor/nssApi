from rest_framework import serializers

from file_uploads.models import UploadPDF


class UploadPDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadPDF
        fields = [
            'id', 'file_name', 'file', 'signature_image',
            'signature_drawing', 'is_signed', 'signed_file', 'uploaded_at'
        ]
        read_only_fields = [
            'id', 'is_signed', 'signed_file', 'uploaded_at',
            'signature_drawing', 'signature_image'
        ]