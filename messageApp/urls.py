

from django.urls import path
from .views import send_message, inbox, sent_messages
from django.urls import path
from .views import send_message, inbox, sent_messages, unread_messages, mark_message_as_read,get_replies, delete_message, view_message, mark_all_as_read

urlpatterns = [
    path('send-message/', send_message, name='send-message'),
    path('inbox/', inbox, name='inbox'),
    path('sent-messages/', sent_messages, name='sent-messages'),
    path('unread-messages/', unread_messages, name='unread-messages'),
    path('mark-message-read/<int:message_id>/', mark_message_as_read, name='mark-message-read'),
    path('delete-message/<int:message_id>/', delete_message, name='delete-message'),
    path('message/<int:message_id>/replies/', get_replies, name='get-replies'), 
    path('view-message/<int:message_id>/', view_message, name='view-message'),
    path('mark-all-read/', mark_all_as_read, name='mark-all-read'), # <-- Add this line
]

