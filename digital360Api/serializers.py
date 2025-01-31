from rest_framework import serializers
from .models import MyUser, Region

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Use `create_user` to ensure password hashing
        password = validated_data.pop('password')
        user = MyUser(**validated_data)
        user.set_password(password)  # Hash password
        user.save()
        return user
    

#Serializer class for Region
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'