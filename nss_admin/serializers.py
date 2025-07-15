from rest_framework import serializers

from nss_admin.models import Administrator
from nss_supervisors.models import Supervisor

class AdministratorSerializer(serializers.ModelSerializer):
    
    assigned_supervisors = serializers.PrimaryKeyRelatedField(queryset=Supervisor.objects.all(),  many=True )
    email = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_gender(self, obj):
        return obj.user.gender if obj.user and hasattr(obj.user, 'gender') else None

    def get_user_type(self, obj):
        return obj.user.user_type if obj.user and hasattr(obj.user, 'user_type') else None

    class Meta:
        model = Administrator
        fields = '__all__'