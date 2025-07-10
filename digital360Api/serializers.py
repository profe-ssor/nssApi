from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import  GhanaCardRecord, MyUser,  OTPVerification, Region,  UniversityRecord,Workplace, GhostDetection
from django.contrib.auth.password_validation import validate_password
from nss_personnel.models import NSSPersonnel
from nss_supervisors.models import Supervisor
from nss_admin.models import Administrator

User = get_user_model()

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

class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        
        # Validate password strength
        validate_password(attrs['new_password'])
        
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        validate_password(attrs['new_password'])
        
        return attrs

class RegionalOverviewSerializer(serializers.Serializer):
    region = serializers.CharField()
    total_personnel = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()
    completed_submissions = serializers.IntegerField()
    supervisor_count = serializers.IntegerField()

class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'email', 'gender', 'user_type', 'created_at']

class NSSPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSSPersonnel
        fields = '__all__'

class SupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supervisor
        fields = '__all__'

class AdministratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = '__all__'

class GhostDetectionSerializer(serializers.ModelSerializer):
    nss_personnel_name = serializers.CharField(source='nss_personnel.full_name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.full_name', read_only=True)
    assigned_admin_name = serializers.CharField(source='assigned_admin.full_name', read_only=True)
    personnel_ghana_card = serializers.CharField(source='nss_personnel.ghana_card_record', read_only=True)
    personnel_nss_id = serializers.CharField(source='nss_personnel.nss_id', read_only=True)
    personnel_region = serializers.CharField(source='nss_personnel.region_of_posting', read_only=True)
    personnel_department = serializers.CharField(source='nss_personnel.department', read_only=True)
    
    class Meta:
        model = GhostDetection
        fields = [
            'id', 'nss_personnel', 'supervisor', 'assigned_admin',
            'detection_flags', 'severity', 'status', 'submission_attempt',
            'timestamp', 'resolved_at', 'resolution_notes', 'admin_action_taken',
            'nss_personnel_name', 'supervisor_name', 'assigned_admin_name',
            'personnel_ghana_card', 'personnel_nss_id', 'personnel_region',
            'personnel_department'
        ]
        read_only_fields = ['timestamp']