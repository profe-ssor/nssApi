from digital360Api.models import MyUser
from nss_personnel.models import NSSPersonnel
from nss_supervisors.models import Supervisor



def get_user_full_name(user):
    if hasattr(user, 'nss_profile'):
        return user.nss_profile.get_full_name()
    elif hasattr(user, 'supervisor_profile'):
        return user.supervisor_profile.get_full_name()
    elif hasattr(user, 'administrator_profile'):
        return user.administrator_profile.get_full_name()
    return user.email or user.username  # fallback


def get_reply_to_sender_name(obj):
    if obj.reply_to:
        return get_user_full_name(obj.reply_to.sender)
    return None


def get_allowed_recipient_ids(user):
    if user.user_type == 'nss':
        try:
            nss_profile = NSSPersonnel.objects.get(user=user)
            recipient_ids = []
            if nss_profile.assigned_supervisor:
                recipient_ids.append(nss_profile.assigned_supervisor.user.id)
            recipient_ids += list(
                MyUser.objects.filter(user_type='admin').values_list('id', flat=True)
            )
            return recipient_ids
        except NSSPersonnel.DoesNotExist:
            return []

    elif user.user_type == 'supervisor':
        try:
            supervisor_profile = Supervisor.objects.get(user=user)
            recipient_ids = list(
                NSSPersonnel.objects.filter(
                    assigned_supervisor=supervisor_profile
                ).values_list('user_id', flat=True)
            )
            recipient_ids += list(
                MyUser.objects.filter(user_type='admin').values_list('id', flat=True)
            )
            return recipient_ids
        except Supervisor.DoesNotExist:
            return []

    elif user.user_type == 'admin':
        return list(
            MyUser.objects.exclude(id=user.id).values_list('id', flat=True)
        )

    return []
