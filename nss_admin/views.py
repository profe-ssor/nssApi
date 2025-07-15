from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

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

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def get_or_update_admin_by_id(request, admin_id):
    try:
        admin = Administrator.objects.get(id=admin_id)
    except Administrator.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=404)

    if request.method == 'GET':
        serializer = AdministratorSerializer(admin)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = AdministratorSerializer(admin, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Update related user fields if present
            user = admin.user
            user_updated = False
            if 'email' in request.data:
                user.email = request.data['email']
                user_updated = True
            if 'gender' in request.data:
                user.gender = request.data['gender']
                user_updated = True
            if user_updated:
                user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

@api_view(['GET'])
def get_admin_by_user_id(request, user_id):
    try:
        admin = Administrator.objects.get(user__id=user_id)
        serializer = AdministratorSerializer(admin)
        return Response(serializer.data)
    except Administrator.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=404)

