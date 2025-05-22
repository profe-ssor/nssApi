def get_user_full_name(user):
    if hasattr(user, 'nss_profile'):
        return user.nss_profile.get_full_name()
    elif hasattr(user, 'supervisor_profile'):
        return user.supervisor_profile.get_full_name()
    elif hasattr(user, 'administrator_profile'):
        return user.administrator_profile.get_full_name()
    return user.email or user.username  # fallback
def get_reply_to_sender_name(self, obj):
    if obj.reply_to:
        return get_user_full_name(obj.reply_to.sender)
    return None
