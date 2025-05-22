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
    attachment_id = request.data.get('attachment')
    reply_to_id = request.data.get('reply_to')

    if not receiver_id:
        return Response({'error': 'Receiver ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        receiver = MyUser.objects.get(id=receiver_id)
    except MyUser.DoesNotExist:
        return Response({'error': 'Receiver not found.'}, status=status.HTTP_404_NOT_FOUND)

    message = Message(
        sender=sender,
        receiver=receiver,
        content=content
    )

    if attachment_id:
        try:
            pdf = UploadPDF.objects.get(id=attachment_id, is_signed=True, user=sender)
            message.attachment = pdf
        except UploadPDF.DoesNotExist:
            return Response({'error': 'Invalid attachment ID or PDF is not signed.'}, status=status.HTTP_400_BAD_REQUEST)

    if reply_to_id:
        try:
            original_message = Message.objects.get(id=reply_to_id)
            message.reply_to = original_message

            # ✅ Mark the original message as read if replying to it
            if original_message.receiver == request.user:
                original_message.is_read = True
                original_message.save()
        except Message.DoesNotExist:
            return Response({'error': 'Reply-to message not found.'}, status=status.HTTP_404_NOT_FOUND)

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
    # ❌ No auto-marking here — frontend must explicitly call mark-as-read


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sent_messages(request):
    user = request.user
    messages = Message.objects.filter(sender=user).order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_messages(request):
    user = request.user
    messages = Message.objects.filter(receiver=user, is_read=False).order_by('-timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


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
    
    # Check if user is sender or receiver
    if message.sender != user and message.receiver != user:
        return Response({'error': 'Not authorized to view this message.'}, status=status.HTTP_403_FORBIDDEN)
    
    # Mark as read if user is the receiver and message is unread
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