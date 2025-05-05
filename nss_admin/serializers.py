from rest_framework import serializers

from nss_admin.models import Administrator
from nss_supervisors.models import Supervisor

class AdministratorSerializer(serializers.ModelSerializer):
    
    assigned_supervisors = serializers.PrimaryKeyRelatedField(queryset=Supervisor.objects.all(),  many=True )

    class Meta:
        model = Administrator
        fields = '__all__'