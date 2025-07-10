# messages/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date
from django.shortcuts import render
from django.core.paginator import Paginator

from file_uploads.models import UploadPDF
from messageApp.utils import get_allowed_recipient_ids
from nss_personnel.models import NSSPersonnel
from nss_supervisors.models import Supervisor
from .models import Message, UserConnection
from .serializers import MessageSerializer, UserConnectionSerializer, MessageStatsSerializer, UserDropdownSerializer, MessageListSerializer
from digital360Api.models import MyUser
from nss_supervisors.views import log_message_sent


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Send a message from one user to another
    """
    data = request.data.copy()
    data['sender'] = request.user.id
    
    # Handle both 'recipient' and 'receiver' field names for backward compatibility
    if 'receiver' in data and 'recipient' not in data:
        data['recipient'] = data['receiver']
    elif 'recipient' in data and 'receiver' not in data:
        data['receiver'] = data['recipient']
    
    serializer = MessageSerializer(data=data)
    if serializer.is_valid():
        message = serializer.save()
        
        # Log the activity if sender is a supervisor
        if request.user.user_type == 'supervisor':
            try:
                recipient_id = data.get('recipient') or data.get('receiver')
                if recipient_id:
                    recipient = MyUser.objects.get(id=recipient_id)
                    log_message_sent(request.user, recipient)
            except MyUser.DoesNotExist:
                pass  # Logging is optional, don't fail if recipient not found
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request):
    """
    Get messages for the current user (sent and received)
    """
    user = request.user
    messages = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient').order_by('-timestamp')
    
    # Apply filters
    message_type = request.GET.get('type')
    if message_type == 'sent':
        messages = messages.filter(sender=user)
    elif message_type == 'received':
        messages = messages.filter(recipient=user)
    
    # Pagination
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))
    
    paginator = Paginator(messages, page_size)
    page_obj = paginator.get_page(page)
    
    serializer = MessageListSerializer(page_obj, many=True)
    
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
def get_message_detail(request, pk):
    """
    Get detailed information about a specific message
    """
    user = request.user
    try:
        message = Message.objects.filter(
            pk=pk
        ).filter(
            Q(sender=user) | Q(recipient=user)
        ).first()
        
        if not message:
            return Response(
                {'error': 'Message not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = MessageSerializer(message)
        return Response(serializer.data)
    except Message.DoesNotExist:
        return Response(
            {'error': 'Message not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_as_read(request, pk):
    """
    Mark a message as read
    """
    user = request.user
    try:
        message = Message.objects.get(
            pk=pk,
            recipient=user,
            is_read=False
        )
        message.is_read = True
        message.save()
        serializer = MessageSerializer(message)
        return Response(serializer.data)
    except Message.DoesNotExist:
        return Response(
            {'error': 'Message not found or already read'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    """
    Get count of unread messages for the current user
    """
    count = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    return Response({'unread_count': count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inbox(request):
    user = request.user
    priority = request.GET.get('priority')
    message_type = request.GET.get('type')
    
    messages = Message.objects.filter(receiver=user)
    
    if priority:
        messages = messages.filter(priority=priority)
    if message_type:
        messages = messages.filter(message_type=message_type)
    
    messages = messages.order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sent_messages(request):
    user = request.user
    priority = request.GET.get('priority')
    message_type = request.GET.get('type')
    
    messages = Message.objects.filter(sender=user)
    
    if priority:
        messages = messages.filter(priority=priority)
    if message_type:
        messages = messages.filter(message_type=message_type)
    
    messages = messages.order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_messages(request):
    user = request.user
    messages = Message.objects.filter(receiver=user, is_read=False).order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_stats(request):
    """Get comprehensive message statistics for the user"""
    user = request.user
    today = date.today()
    
    # Base queryset for received messages
    received_messages = Message.objects.filter(receiver=user)
    
    stats = {
        'total_messages': received_messages.count(),
        'unread_messages': received_messages.filter(is_read=False).count(),
        'today_messages': received_messages.filter(timestamp__date=today).count(),
        'high_priority': received_messages.filter(priority='high').count(),
        'medium_priority': received_messages.filter(priority='medium').count(),
        'low_priority': received_messages.filter(priority='low').count(),
        'inquiry_count': received_messages.filter(message_type='inquiry').count(),
        'feedback_count': received_messages.filter(message_type='feedback').count(),
        'report_count': received_messages.filter(message_type='report').count(),
    }
    
    serializer = MessageStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_message_as_read(request, message_id):
    user = request.user
    try:
        message = Message.objects.get(id=message_id, receiver=user)
    except Message.DoesNotExist:
        return Response({
            'error': 'Message not found or not authorized.'
        }, status=status.HTTP_404_NOT_FOUND)

    message.is_read = True
    message.save()

    return Response({'success': 'Message marked as read.'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    user = request.user
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)

    if message.sender != user and message.receiver != user:
        return Response({
            'error': 'You are not authorized to delete this message.'
        }, status=status.HTTP_403_FORBIDDEN)

    message.delete()
    return Response({
        'success': 'Message deleted successfully.'
    }, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_replies(request, message_id):
    try:
        parent = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)

    replies = parent.replies.all().order_by('timestamp')
    serializer = MessageSerializer(replies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_message(request, message_id):
    user = request.user
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    if message.sender != user and message.receiver != user:
        return Response({
            'error': 'Not authorized to view this message.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if message.receiver == user and not message.is_read:
        message.is_read = True
        message.save()
    
    serializer = MessageSerializer(message)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    user = request.user
    updated_count = Message.objects.filter(
        receiver=user, 
        is_read=False
    ).update(is_read=True)
    
    return Response({
        'success': f'{updated_count} messages marked as read.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def priority_messages(request, priority):
    """Get messages by priority (high, medium, low)"""
    user = request.user
    if priority not in ['high', 'medium', 'low']:
        return Response({
            'error': 'Invalid priority. Must be high, medium, or low.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    messages = Message.objects.filter(
        receiver=user, 
        priority=priority
    ).order_by('-timestamp')
    
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_messages(request):
    """Get today's messages"""
    user = request.user
    today = date.today()
    
    messages = Message.objects.filter(
        receiver=user,
        timestamp__date=today
    ).order_by('-timestamp')
    
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_connections(request):
    """List all user connections (admin only)"""
    connections = UserConnection.objects.all()
    serializer = UserConnectionSerializer(connections, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_recipients(request):
    user = request.user
    user_type = user.user_type  # 'nss', 'supervisor', 'admin'

    recipients = []

    if user_type == 'nss':
        try:
            nss_profile = NSSPersonnel.objects.get(user=user)
            if nss_profile.assigned_supervisor:
                recipients.append(nss_profile.assigned_supervisor.user)
        except NSSPersonnel.DoesNotExist:
            pass
        recipients += list(MyUser.objects.filter(user_type='admin'))

    elif user_type == 'supervisor':
        try:
            supervisor_profile = Supervisor.objects.get(user=user)
            nss_users = NSSPersonnel.objects.filter(assigned_supervisor=supervisor_profile).values_list('user', flat=True)
            recipients += list(MyUser.objects.filter(id__in=nss_users))
        except Supervisor.DoesNotExist:
            pass
        recipients += list(MyUser.objects.filter(user_type='admin'))

    elif user_type == 'admin':
        recipients += list(MyUser.objects.filter(user_type__in=['nss', 'supervisor']))

    # Remove duplicates while preserving order
    seen_ids = set()
    unique_recipients = []
    for r in recipients:
        if r.id not in seen_ids:
            unique_recipients.append(r)
            seen_ids.add(r.id)

    serializer = UserDropdownSerializer(unique_recipients, many=True)
    return Response(serializer.data)
