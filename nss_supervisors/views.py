from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework.decorators import api_view
from rest_framework import status

from digital360Api.models import MyUser
from nss_supervisors.models import Supervisor
from nss_supervisors.serializers import SupervisorSerializer

# Create your views here.
# Endpoints for Supervisors Database
@api_view(['POST'])
def SupervisorsDatabase(request):
    data = request.data
    user_id = data.get('user_id')
    try:
        user = MyUser.objects.get(id=user_id) 
    except MyUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    data['user'] = user.id 
    serializer = SupervisorSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": 'Data saved successfully'
            }, status=status.HTTP_201_CREATED
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Endpoint to get all Supervisors
@api_view(['GET'])
def get_all_SupervisorsDataBase(request):
    supervisors = Supervisor.objects.all()
    serializer = SupervisorSerializer(supervisors, many=True)
    return Response(serializer.data)

# Endpoint to count all Supervisors
@api_view(['GET'])
def count_SupervisorsDataBase(request):
    count = Supervisor.objects.all().count()
    return Response({"count": count})


