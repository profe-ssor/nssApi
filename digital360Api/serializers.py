from rest_framework import serializers
from .models import MyUser, OTPVerification, Region, UploadPDF


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Ensure password is hashed
        return MyUser.objects.create_user(**validated_data)

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPVerification
        fields = ['user', 'otp_code', 'is_used', 'created_at', 'expires_at']
        extra_kwargs = {'otp_code': {'write_only': True}}

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

# serializers.py
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