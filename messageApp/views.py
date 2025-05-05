# in views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from file_uploads.models import UploadPDF

from .models import Message
from .serializers import MessageSerializer
from digital360Api.models import MyUser

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    sender = request.user
    receiver_id = request.data.get('receiver')
    content = request.data.get('content')
    attachment_id = request.data.get('attachment')  # Change to get the ID from data
    
    if not receiver_id:
        return Response({'error': 'Receiver ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        receiver = MyUser.objects.get(id=receiver_id)
    except MyUser.DoesNotExist:
        return Response({'error': 'Receiver not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Create the message object
    message = Message(
        sender=sender,
        receiver=receiver,
        content=content
    )
    
    # Handle the attachment if it's a PDF ID
    if attachment_id:
        try:
            pdf = UploadPDF.objects.get(id=attachment_id, is_signed=True, user=sender)
            message.attachment = pdf
        except UploadPDF.DoesNotExist:
            return Response({'error': 'Invalid attachment ID or PDF is not signed.'}, status=status.HTTP_400_BAD_REQUEST)
    
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
    messages = Message.objects.filter(receiver=user).order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sent_messages(request):
    user = request.user
    messages = Message.objects.filter(sender=user).order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

#  Unread Messages View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_messages(request):
    user = request.user
    messages = Message.objects.filter(receiver=user, is_read=False).order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

#  Filter Inbox by read Messages
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_message_as_read(request, message_id):
    user = request.user
    try:
        message = Message.objects.get(id=message_id, receiver=user)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found or not authorized.'}, status=status.HTTP_404_NOT_FOUND)

    message.is_read = True
    message.save()

    return Response({'success': 'Message marked as read.'}, status=status.HTTP_200_OK)

# Delete Message (Sender or Receiver)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    user = request.user
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)

    if message.sender != user and message.receiver != user:
        return Response({'error': 'You are not authorized to delete this message.'}, status=status.HTTP_403_FORBIDDEN)

    message.delete()
    return Response({'success': 'Message deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

