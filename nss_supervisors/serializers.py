from rest_framework import serializers 
from digital360Api.models import Workplace
from nss_personnel.serializer import NSSPersonnelSerializer
from nss_supervisors.models import Supervisor
from .models import ActivityLog


class SupervisorSerializer(serializers.ModelSerializer):
    assigned_workplace = serializers.StringRelatedField(source='assigned_workplace.workplace_name')
    assigned_region = serializers.StringRelatedField(source='assigned_region.name')
    supervised_nss_personnel = NSSPersonnelSerializer(many=True, read_only=True)
    class Meta:
        model = Supervisor
        fields = '__all__'


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'

