from rest_framework import serializers
from .models import  GhanaCardRecord, MyUser,  OTPVerification, Region,  UniversityRecord,Workplace




class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class GhanaCardRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GhanaCardRecord
        fields = '__all__'

class WorkplaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workplace
        fields = '__all__'


class UniversityRecordSerializer(serializers.ModelSerializer):
    ghana_card_number = GhanaCardRecordSerializer()
    
    class Meta:
        model = UniversityRecord
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['email', 'username', 'password', 'gender', 'user_type']  # Use 'user_type' instead of 'role'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user_type = validated_data.pop('user_type', 'nss')  # Default to 'nss' if not provided
        user = MyUser.objects.create_user(**validated_data)
        user.user_type = user_type  # Assign the user_type correctly
        user.save()
        return user

class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPVerification
        fields = ['user', 'otp_code', 'is_used', 'created_at', 'expires_at']
        extra_kwargs = {'otp_code': {'write_only': True}}

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

# serializers.py