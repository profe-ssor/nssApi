from django.shortcuts import render
from rest_framework.response import Response 

from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from digital360Api.models import MyUser
from digital360Api.serializers import UserSerializer
from nss_admin.models import Administrator
from nss_admin.serializers import AdministratorSerializer
from nss_personnel.models import NSSPersonnel
from nss_personnel.serializer import NSSPersonnelSerializer
from nss_supervisors.serializers import SupervisorSerializer

    
# Enpoint for savin NssPersonel Database

@api_view(['POST'])
def NssPersonelDatabase(request):
    data = request.data
    user_id = data.get('user_id') 

    try:
        user = MyUser.objects.get(id=user_id) 
    except MyUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    data['user'] = user.id  

    serializer = NSSPersonnelSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Data saved successfully',
            'full_name': serializer.instance.full_name,
            }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Endpoint to get all NssPersonel
@api_view(['GET'])
def get_all_NssPersonelDataBase(request):
    nss_personel = NSSPersonnel.objects.all()
    serializer = NSSPersonnelSerializer(nss_personel, many=True)
    return Response(serializer.data)

# Endpoint to count all NssPersonel
@api_view(['GET'])
def count_NssPersonelDataBase(request):
    count = NSSPersonnel.objects.all().count()
    return Response({"count": count})

# endpoint to return all nssmembers 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nssmembers(request):
    normal_users = MyUser.objects.filter(is_superuser=False, is_staff=False)
    serializer = UserSerializer(normal_users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def count_NssPersonelDataBase(request):
    count = NSSPersonnel.objects.all().count()
    return Response({"count": count})

# Get NSS's Assigned Supervisor

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_supervisor(request):
    user = request.user
    try:
        nss_personnel = NSSPersonnel.objects.get(user=user)
        supervisor = nss_personnel.assigned_supervisor
        if not supervisor:
            return Response({'error': 'No supervisor assigned.'}, status=status.HTTP_404_NOT_FOUND)
        
    
        serializer = SupervisorSerializer(supervisor)
        return Response(serializer.data)
    except NSSPersonnel.DoesNotExist:
        return Response({'error': 'NSS Personnel profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    
# Get  NSS's Assigned Admin (Through Supervisor)
# Fetch NSS Personnel's assigned Admin
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_admin(request):
    try:
        nss_personnel = NSSPersonnel.objects.get(user=request.user)
        supervisor = nss_personnel.assigned_supervisor
        if supervisor:
            # Fetch the admin who assigned this supervisor (if relation exists)
            admins = Administrator.objects.filter(assigned_supervisors=supervisor)
            if admins.exists():
                admin_serializer = AdministratorSerializer(admins.first())  # Get first admin
                return Response(admin_serializer.data)
            else:
                return Response({'error': 'No admin found for this supervisor'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'No supervisor assigned to you'}, status=status.HTTP_404_NOT_FOUND)
    except NSSPersonnel.DoesNotExist:
        return Response({'error': 'NSS personnel not found'}, status=status.HTTP_404_NOT_FOUND)
