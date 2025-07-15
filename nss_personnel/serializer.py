from rest_framework import serializers

from digital360Api.models import Region
from nss_personnel.models import NSSPersonnel
from evaluations.models import Evaluation
from file_uploads.models import UploadPDF
from digital360Api.models import UniversityRecord, GhanaCardRecord
from digital360Api.serializers import UniversityRecordSerializer

class NSSPersonnelSerializer(serializers.ModelSerializer):
    region_name = serializers.SerializerMethodField()
    region_of_posting = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())
    user_id = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    total_submissions = serializers.SerializerMethodField()
    approved_submissions = serializers.SerializerMethodField()
    pending_submissions = serializers.SerializerMethodField()
    rejected_submissions = serializers.SerializerMethodField()
    university_record = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    ghana_card_address = serializers.SerializerMethodField()

    def get_region_name(self, obj):
        return obj.region_of_posting.name if obj.region_of_posting else None

    def get_user_id(self, obj):
        return obj.user.id if obj.user else None

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_total_submissions(self, obj):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            eval_count = Evaluation.objects.filter(nss_personnel=obj.user, supervisor=request.user).count()
            pdf_count = UploadPDF.objects.filter(user=obj.user, receiver=request.user, form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']).count()
            return eval_count + pdf_count
        return Evaluation.objects.filter(nss_personnel=obj.user).count()

    def get_approved_submissions(self, obj):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            eval_count = Evaluation.objects.filter(nss_personnel=obj.user, supervisor=request.user, status='approved').count()
            pdf_count = UploadPDF.objects.filter(user=obj.user, receiver=request.user, status='approved', form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']).count()
            return eval_count + pdf_count
        return Evaluation.objects.filter(nss_personnel=obj.user, status='approved').count()

    def get_pending_submissions(self, obj):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            eval_count = Evaluation.objects.filter(nss_personnel=obj.user, supervisor=request.user, status='pending').count()
            pdf_count = UploadPDF.objects.filter(user=obj.user, receiver=request.user, status='pending', form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']).count()
            return eval_count + pdf_count
        return Evaluation.objects.filter(nss_personnel=obj.user, status='pending').count()

    def get_rejected_submissions(self, obj):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            eval_count = Evaluation.objects.filter(nss_personnel=obj.user, supervisor=request.user, status='rejected').count()
            pdf_count = UploadPDF.objects.filter(user=obj.user, receiver=request.user, status='rejected', form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']).count()
            return eval_count + pdf_count
        return Evaluation.objects.filter(nss_personnel=obj.user, status='rejected').count()

    def get_university_record(self, obj):
        try:
            ghana_card = GhanaCardRecord.objects.get(ghana_card_number=obj.ghana_card_record)
            uni = UniversityRecord.objects.get(ghana_card_number=ghana_card)
            return UniversityRecordSerializer(uni).data
        except (GhanaCardRecord.DoesNotExist, UniversityRecord.DoesNotExist):
            return None

    def get_supervisor_name(self, obj):
        if obj.assigned_supervisor and hasattr(obj.assigned_supervisor, 'full_name'):
            return obj.assigned_supervisor.full_name
        return None

    def get_ghana_card_address(self, obj):
        try:
            from digital360Api.models import GhanaCardRecord
            ghana_card = GhanaCardRecord.objects.get(ghana_card_number=obj.ghana_card_record)
            return ghana_card.address
        except Exception:
            return None

    class Meta:
        model = NSSPersonnel
        fields = '__all__'
        extra_fields = ['user_id', 'email', 'total_submissions', 'approved_submissions', 'pending_submissions', 'rejected_submissions', 'university_record', 'supervisor_name', 'ghana_card_address']
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



