from rest_framework import serializers
from .models import Administrator, GhanaCardRecord, MyUser, NSSPersonnel, OTPVerification, Region, Supervisor, UniversityRecord, UploadPDF, Workplace




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

class SupervisorSerializer(serializers.ModelSerializer):
    ghana_card_record = serializers.PrimaryKeyRelatedField(queryset=GhanaCardRecord.objects.all()) # Nested serialization
    assigned_workplace = serializers.PrimaryKeyRelatedField(queryset=Workplace.objects.all())

    class Meta:
        model = Supervisor
        fields = '__all__'


class AdministratorSerializer(serializers.ModelSerializer):
    ghana_card_record = serializers.PrimaryKeyRelatedField(queryset=GhanaCardRecord.objects.all())
    assigned_supervisors = serializers.PrimaryKeyRelatedField(queryset=Supervisor.objects.all(),  many=True )

    class Meta:
        model = Administrator
        fields = '__all__'

class NSSPersonnelSerializer(serializers.ModelSerializer):
    region_of_posting = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())

    class Meta:
        model = NSSPersonnel
        fields = '__all__'

    # def validate_ghana_card_record(self, value):
    #     """Ensure Ghana Card exists in the database before allowing submission."""
    #     if not GhanaCardRecord.objects.filter(ghana_card_number=value).exists():
    #         raise serializers.ValidationError("Invalid Ghana Card number! Please enter a valid one.")
    #     return value


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