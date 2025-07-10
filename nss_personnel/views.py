from django.shortcuts import render
from rest_framework.response import Response 

from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from digital360Api.models import MyUser
from digital360Api.permissions import IsAdmin, IsSupervisor
from digital360Api.serializers import UserSerializer
from nss_admin.models import Administrator
from nss_admin.serializers import AdministratorSerializer
from nss_personnel.models import NSSPersonnel
from nss_personnel.serializer import AdminUpdateNSSPersonnelSerializer, NSSPersonnelSerializer, SupervisorUpdateNSSPersonnelSerializer, NSSPersonnelListSerializer
from nss_supervisors.models import Supervisor
from nss_supervisors.serializers import SupervisorSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from nss_supervisors.models import Supervisor
from nss_supervisors.serializers import SupervisorSerializer
from nss_personnel.serializer import NSSPersonnelSerializer
from django.core.paginator import Paginator
from nss_supervisors.views import log_personnel_assignment

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
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_update_nss(request, nss_id):
    try:
        nss = NSSPersonnel.objects.get(id=nss_id)
    except NSSPersonnel.DoesNotExist:
        return Response({'error': 'NSS Personnel not found'}, status=404)

    serializer = AdminUpdateNSSPersonnelSerializer(nss, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Status and performance updated by admin'})
    return Response(serializer.errors, status=400)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsSupervisor])
def supervisor_update_performance(request, nss_id):
    try:
        nss = NSSPersonnel.objects.get(id=nss_id)
    except NSSPersonnel.DoesNotExist:
        return Response({'error': 'NSS Personnel not found'}, status=404)

    serializer = SupervisorUpdateNSSPersonnelSerializer(nss, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Performance updated by supervisor'})
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_by_status(request):
    result = NSSPersonnel.objects.values('status').annotate(total=Count('id'))
    return Response(result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_by_performance(request):
    result = NSSPersonnel.objects.values('performance').annotate(total=Count('id'))
    return Response(result)

# get all assined nss of a specific supervisor or admin 

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from nss_supervisors.models import Supervisor
from nss_supervisors.serializers import SupervisorSerializer
from nss_personnel.serializer import NSSPersonnelSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grouped_by_supervisor(request):
    supervisors = Supervisor.objects.prefetch_related('nss_personnel')  # using related_name
    grouped_data = []

    for supervisor in supervisors:
        nss_assigned = supervisor.nss_personnel.all()  # reverse relation using related_name
        nss_data = NSSPersonnelSerializer(nss_assigned, many=True).data
        supervisor_data = SupervisorSerializer(supervisor).data
        supervisor_data['assigned_nss'] = nss_data  # attach NSS data to supervisor
        grouped_data.append(supervisor_data)

    return Response(grouped_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nss_grouped_by_admin(request):
    admins = Administrator.objects.prefetch_related('assigned_supervisors__nsspersonnel_set')
    data = []

    for admin in admins:
        admin_group = {
            'admin_id': admin.id,
            'admin_name': admin.full_name,
            'supervisors': []
        }
        for supervisor in admin.assigned_supervisors.all():
            nss_personnel = supervisor.nsspersonnel_set.all()
            personnel_data = NSSPersonnelSerializer(nss_personnel, many=True).data
            admin_group['supervisors'].append({
                'supervisor_id': supervisor.id,
                'supervisor_name': supervisor.full_name,
                'nss_personnel': personnel_data
            })

        data.append(admin_group)

    return Response(data, status=status.HTTP_200_OK)

# Count them 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_nss_by_supervisor(request):
    supervisors = Supervisor.objects.prefetch_related('nss_personnel')
    counts = []

    for supervisor in supervisors:
        count = supervisor.nss_personnel.count()
        counts.append({
            'supervisor_id': supervisor.id,
            'supervisor_name': supervisor.full_name,
            'nss_count': count
        })

    return Response(counts, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_nss_by_admin(request):
    admins = Administrator.objects.prefetch_related('assigned_supervisors__nss_personnel')
    result = []

    for admin in admins:
        total_nss = 0
        admin_data = {
            'admin_id': admin.id,
            'admin_name': admin.full_name,
            'nss_count': 0
        }

        for supervisor in admin.assigned_supervisors.all():
            total_nss += supervisor.nss_personnel.count()

        admin_data['nss_count'] = total_nss
        result.append(admin_data)

    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
def department_choices(request):
    from nss_personnel.models import NSSPersonnel
    return Response([
        {"value": value, "label": label}
        for value, label in NSSPersonnel.DEPARTMENT_CHOICES
    ])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_by_status_for_supervisor(request):
    user = request.user
    personnel = NSSPersonnel.objects.filter(assigned_supervisor__user=user)
    result = personnel.values('status').annotate(total=Count('id'))
    return Response(result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_by_performance_for_supervisor(request):
    user = request.user
    personnel = NSSPersonnel.objects.filter(assigned_supervisor__user=user)
    result = personnel.values('performance').annotate(total=Count('id'))
    return Response(result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assigned_personnel_details(request):
    user = request.user
    # If user is a supervisor, show their assigned personnel
    personnel = NSSPersonnel.objects.filter(assigned_supervisor__user=user)
    # If user is an admin, show all personnel assigned to supervisors they manage
    if hasattr(user, 'administrator_profile'):
        admin = user.administrator_profile
        supervisor_ids = admin.assigned_supervisors.values_list('id', flat=True)
        personnel = NSSPersonnel.objects.filter(assigned_supervisor__id__in=supervisor_ids)
    serializer = NSSPersonnelSerializer(personnel, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def performance_choices(request):
    from nss_personnel.models import NSSPersonnel
    return Response([
        {"value": value, "label": label}
        for value, label in NSSPersonnel.PERFORMANCE_CHOICES
    ])

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_personnel(request):
    """
    Create a new NSS personnel
    """
    data = request.data.copy()
    
    serializer = NSSPersonnelSerializer(data=data)
    if serializer.is_valid():
        personnel = serializer.save()
        
        # Log the activity if user is a supervisor
        if request.user.user_type == 'supervisor':
            log_personnel_assignment(request.user, personnel)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personnel_list(request):
    """
    Get list of NSS personnel
    """
    personnel = NSSPersonnel.objects.all().order_by('-created_at')
    
    # Apply filters
    department = request.GET.get('department')
    if department:
        personnel = personnel.filter(department=department)
    
    status_filter = request.GET.get('status')
    if status_filter:
        personnel = personnel.filter(status=status_filter)
    
    # Pagination
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))
    
    paginator = Paginator(personnel, page_size)
    page_obj = paginator.get_page(page)
    
    serializer = NSSPersonnelListSerializer(page_obj, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personnel_detail(request, pk):
    """
    Get detailed information about a specific personnel
    """
    try:
        personnel = NSSPersonnel.objects.get(pk=pk)
        serializer = NSSPersonnelSerializer(personnel)
        return Response(serializer.data)
    except NSSPersonnel.DoesNotExist:
        return Response(
            {'error': 'Personnel not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_personnel(request, pk):
    """
    Update personnel information
    """
    try:
        personnel = NSSPersonnel.objects.get(pk=pk)
        serializer = NSSPersonnelSerializer(
            personnel, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except NSSPersonnel.DoesNotExist:
        return Response(
            {'error': 'Personnel not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_personnel(request, pk):
    """
    Delete a personnel record
    """
    try:
        personnel = NSSPersonnel.objects.get(pk=pk)
        personnel.delete()
        return Response({'message': 'Personnel deleted successfully'})
    except NSSPersonnel.DoesNotExist:
        return Response(
            {'error': 'Personnel not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
