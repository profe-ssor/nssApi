from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework.decorators import api_view
from rest_framework import status

from digital360Api.models import MyUser
from nss_admin.models import Administrator
from nss_admin.serializers import AdministratorSerializer

# Create your views here.
# Endpoints for Administrator Database
@api_view(['POST'])
def AdministratorsDatabase(request):
    data = request.data
    user_id = data.get('user_id')
    try:
        user = MyUser.objects.get(id=user_id) 
    except MyUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    data['user'] = user.id 
    serializer =  AdministratorSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": 'Data saved successfully',
                   'id': serializer.instance.id, 
            }, status=status.HTTP_201_CREATED
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Endpoint to get all Administrators
@api_view(['GET'])
def get_all_AdministratorsDataBase(request):
    administrators = Administrator.objects.all()
    serializer = AdministratorSerializer(administrators, many=True)
    return Response(serializer.data)

# Endpoint to count all Administrators
@api_view(['GET'])
def count_AdministratorsDataBase(request):
    count = Administrator.objects.all().count()
    return Response({"count": count})

