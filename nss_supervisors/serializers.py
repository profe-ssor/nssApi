

from rest_framework import serializers 
from digital360Api.models import Workplace
from nss_personnel.serializer import NSSPersonnelSerializer
from nss_supervisors.models import Supervisor


class SupervisorSerializer(serializers.ModelSerializer):
    assigned_workplace = serializers.PrimaryKeyRelatedField(queryset=Workplace.objects.all())
    supervised_nss_personnel = NSSPersonnelSerializer(many=True, read_only=True)
    class Meta:
        model = Supervisor
        fields = '__all__'

