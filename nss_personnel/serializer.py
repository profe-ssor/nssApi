from rest_framework import serializers

from digital360Api.models import Region
from nss_personnel.models import NSSPersonnel


class NSSPersonnelSerializer(serializers.ModelSerializer):
    region_of_posting = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())

    class Meta:
        model = NSSPersonnel
        fields = '__all__'
