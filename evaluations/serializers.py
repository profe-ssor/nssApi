from datetime import timezone
from rest_framework import serializers
from .models import Evaluation

class EvaluationListSerializer(serializers.ModelSerializer):
    nss_personnel_name = serializers.CharField(source='nss_personnel.get_full_name', read_only=True)
    nss_personnel_email = serializers.CharField(source='nss_personnel.email', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    administrator_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    completed_today = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_evaluation_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Evaluation
        fields = [
            'id', 'title', 'description', 'evaluation_type', 'type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'nss_personnel_name', 'nss_personnel_email', 'supervisor_name', 'administrator_name',
            'created_at', 'updated_at', 'due_date', 'is_overdue', 
            'completed_today', 'supervisor_comments'
        ]

class EvaluationDetailSerializer(serializers.ModelSerializer):
    nss_personnel_name = serializers.CharField(source='nss_personnel.get_full_name', read_only=True)
    nss_personnel_email = serializers.CharField(source='nss_personnel.email', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    supervisor_email = serializers.CharField(source='supervisor.email', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_evaluation_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Evaluation
        fields = '__all__'

class EvaluationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ['status', 'supervisor_comments']
        
    def update(self, instance, validated_data):
        # Set reviewed_at when status changes to approved/rejected
        if validated_data.get('status') in ['approved', 'rejected']:
            validated_data['reviewed_at'] = timezone.now()
        return super().update(instance, validated_data)

class BulkStatusUpdateSerializer(serializers.Serializer):
    evaluation_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    supervisor_comments = serializers.CharField(required=False, allow_blank=True)

class DashboardStatsSerializer(serializers.Serializer):
    total_submissions = serializers.IntegerField()
    total_pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    overdue = serializers.IntegerField()
    under_review = serializers.IntegerField()
    completed_today = serializers.IntegerField()
