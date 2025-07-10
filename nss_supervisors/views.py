from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from digital360Api.models import MyUser
from nss_supervisors.models import Supervisor
from nss_supervisors.serializers import SupervisorSerializer
from .models import ActivityLog
from .serializers import ActivityLogSerializer

# Helper functions to log supervisor activities
def log_supervisor_activity(supervisor, action, title, description, personnel=None, priority='medium'):
    """Helper function to log supervisor activities"""
    ActivityLog.objects.create(
        supervisor=supervisor,
        action=action,
        title=title,
        description=description,
        personnel=personnel,
        priority=priority
    )

def log_evaluation_approval(supervisor, evaluation):
    """Log when a supervisor approves/rejects an evaluation"""
    action = 'approval' if evaluation.status == 'approved' else 'submission'
    title = f"Evaluation {evaluation.status.title()}"
    description = f"{evaluation.status.title()} evaluation: {evaluation.title}"
    personnel = evaluation.nss_personnel.get_full_name() if evaluation.nss_personnel else 'Unknown'
    
    log_supervisor_activity(supervisor, action, title, description, personnel)

def log_evaluation_review_start(supervisor, evaluation):
    """Log when a supervisor starts reviewing an evaluation"""
    title = "Evaluation Review Started"
    description = f"Started review of evaluation: {evaluation.title}"
    personnel = evaluation.nss_personnel.get_full_name() if evaluation.nss_personnel else 'Unknown'
    
    log_supervisor_activity(supervisor, 'submission', title, description, personnel)

def log_personnel_assignment(supervisor, personnel):
    """Log when a supervisor is assigned personnel"""
    title = "Personnel Assignment"
    description = f"Assigned {personnel.get_full_name()} to supervision"
    log_supervisor_activity(supervisor, 'personnel', title, description, personnel.get_full_name())

def log_message_sent(supervisor, recipient):
    """Log when a supervisor sends a message"""
    title = "Message Sent"
    description = f"Sent message to {recipient.get_full_name()}"
    log_supervisor_activity(supervisor, 'message', title, description, recipient.get_full_name())

def log_document_upload(supervisor, document_name, personnel=None):
    """Log when a supervisor uploads a document"""
    title = "Document Uploaded"
    description = f"Uploaded document: {document_name}"
    log_supervisor_activity(supervisor, 'submission', title, description, personnel)

def log_status_update(supervisor, action_type, details, personnel=None):
    """Log general status updates"""
    title = f"{action_type.title()} Update"
    description = details
    log_supervisor_activity(supervisor, 'submission', title, description, personnel)

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

# Endpoint to update a supervisor
@api_view(['PUT'])
def update_supervisor(request, user_id):
    try:
        supervisor = Supervisor.objects.get(user_id=user_id)
    except Supervisor.DoesNotExist:
        return Response({'error': 'Supervisor not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SupervisorSerializer(supervisor, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Supervisor updated successfully'}, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Endpoint to count all Supervisors
@api_view(['GET'])
def count_SupervisorsDataBase(request):
    count = Supervisor.objects.all().count()
    return Response({"count": count})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supervisor_recent_activity(request):
    user = request.user
    if user.user_type != 'supervisor':
        return Response({'error': 'Only supervisors can access this endpoint'}, status=403)
    activities = ActivityLog.objects.filter(supervisor=user).order_by('-timestamp')[:15]
    serializer = ActivityLogSerializer(activities, many=True)
    return Response(serializer.data)


