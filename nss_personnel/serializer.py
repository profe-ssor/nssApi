from rest_framework import serializers

from digital360Api.models import Region
from nss_personnel.models import NSSPersonnel
from evaluations.models import Evaluation

class NSSPersonnelSerializer(serializers.ModelSerializer):
    region_name = serializers.SerializerMethodField()
    region_of_posting = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())
    user_id = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    total_submissions = serializers.SerializerMethodField()
    approved_submissions = serializers.SerializerMethodField()
    pending_submissions = serializers.SerializerMethodField()
    rejected_submissions = serializers.SerializerMethodField()

    def get_region_name(self, obj):
        return obj.region_of_posting.name if obj.region_of_posting else None

    def get_user_id(self, obj):
        return obj.user.id if obj.user else None

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_total_submissions(self, obj):
        return Evaluation.objects.filter(nss_personnel=obj.user).count()

    def get_approved_submissions(self, obj):
        return Evaluation.objects.filter(nss_personnel=obj.user, status='approved').count()

    def get_pending_submissions(self, obj):
        return Evaluation.objects.filter(nss_personnel=obj.user, status='pending').count()

    def get_rejected_submissions(self, obj):
        return Evaluation.objects.filter(nss_personnel=obj.user, status='rejected').count()

    class Meta:
        model = NSSPersonnel
        fields = '__all__'
        extra_fields = ['user_id', 'email', 'total_submissions', 'approved_submissions', 'pending_submissions', 'rejected_submissions']
        read_only_fields = ['status', 'performance']
        
class AdminUpdateNSSPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSSPersonnel
        fields = ['status', 'performance']
        
class SupervisorUpdateNSSPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSSPersonnel
        fields = ['performance']


class NSSPersonnelListSerializer(serializers.ModelSerializer):
    """Serializer for listing NSS personnel with basic information"""
    region_name = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = NSSPersonnel
        fields = [
            'id', 'user_id', 'email', 'full_name', 'nss_id', 'phone',
            'region_of_posting', 'region_name', 'assigned_institution',
            'status', 'performance', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_region_name(self, obj):
        return obj.region_of_posting.name if obj.region_of_posting else None

    def get_user_id(self, obj):
        return obj.user.id if obj.user else None

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return None



