# messages/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date

from file_uploads.models import UploadPDF
from messageApp.utils import get_allowed_recipient_ids
from nss_personnel.models import NSSPersonnel
from nss_supervisors.models import Supervisor
from .models import Message, UserConnection
from .serializers import MessageSerializer, UserConnectionSerializer, MessageStatsSerializer, UserDropdownSerializer
from digital360Api.models import MyUser


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    sender = request.user
    receiver_id = request.data.get('receiver')
    subject = request.data.get('subject', '')
    content = request.data.get('content')
    attachment_id = request.data.get('attachment')
    reply_to_id = request.data.get('reply_to')
    forward_from_id = request.data.get('forward_from')
    priority = request.data.get('priority', 'medium')
    message_type = request.data.get('message_type', 'inquiry')

    if not receiver_id:
        return Response({'error': 'Receiver ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        receiver = MyUser.objects.get(id=receiver_id)
    except MyUser.DoesNotExist:
        return Response({'error': 'Receiver not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if sender can message the receiver
    # Check if receiver is in allowed recipient list
    allowed_recipient_ids = get_allowed_recipient_ids(sender)
    if receiver.id not in allowed_recipient_ids:
        return Response({
            'error': 'You are not authorized to send messages to this user.'
        }, status=status.HTTP_403_FORBIDDEN)

    

    message = Message(
        sender=sender,
        receiver=receiver,
        subject=subject,
        content=content,
        priority=priority,
        message_type=message_type
    )

    if attachment_id:
        try:
            pdf = UploadPDF.objects.get(id=attachment_id, is_signed=True, user=sender)
            message.attachment = pdf
        except UploadPDF.DoesNotExist:
            return Response({
                'error': 'Invalid attachment ID or PDF is not signed.'
            }, status=status.HTTP_400_BAD_REQUEST)

    if reply_to_id:
        try:
            original_message = Message.objects.get(id=reply_to_id)
            message.reply_to = original_message

            if original_message.receiver == request.user:
                original_message.is_read = True
                original_message.save()
        except Message.DoesNotExist:
            return Response({
                'error': 'Reply-to message not found.'
            }, status=status.HTTP_404_NOT_FOUND)

    # Handle message forwarding
    if forward_from_id:
        try:
            forwarded_message = Message.objects.get(id=forward_from_id)
            # Check if user has permission to forward this message
            if forwarded_message.sender != sender and forwarded_message.receiver != sender:
                return Response({
                    'error': 'You can only forward messages you sent or received.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            message.forwarded_from = forwarded_message
            message.is_forwarded = True
            # If forwarding, prepend "Forwarded: " to content if not already there
            if not content.startswith('Forwarded: '):
                message.content = f"Forwarded: {content}"
        except Message.DoesNotExist:
            return Response({
                'error': 'Message to forward not found.'
            }, status=status.HTTP_404_NOT_FOUND)

    message.save()
    serializer = MessageSerializer(message)

    return Response({
        'success': 'Message sent successfully.',
        'message': serializer.data
    }, status=status.HTTP_201_CREATED)


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
