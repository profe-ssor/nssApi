from rest_framework import serializers

from digital360Api.models import Region
from nss_personnel.models import NSSPersonnel

class NSSPersonnelSerializer(serializers.ModelSerializer):
    region_of_posting = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())

    class Meta:
        model = NSSPersonnel
        fields = '__all__'
        read_only_fields = ['status', 'performance']
        
class AdminUpdateNSSPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSSPersonnel
        fields = ['status', 'performance']
        
class SupervisorUpdateNSSPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSSPersonnel
        fields = ['performance']



