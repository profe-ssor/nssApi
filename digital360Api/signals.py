from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import MyUser

@receiver(post_save, sender=MyUser)
def update_user_role(sender, instance, created, **kwargs):
    """
    Signal that listens for changes in user roles and updates them accordingly.
    """
    if created:
        return  # Prevent running on user creation

    try:
        if instance.is_superuser:
            admin_group, _ = Group.objects.get_or_create(name="Admin")
            instance.groups.add(admin_group)
            print(f"User {instance.email} added to Admin group.")
        
        elif instance.is_staff:
            supervisor_group, _ = Group.objects.get_or_create(name="Supervisor")
            instance.groups.add(supervisor_group)
            print(f"User {instance.email} added to Supervisor group.")
        
        else:
            normal_group, _ = Group.objects.get_or_create(name="Normal User")
            instance.groups.add(normal_group)
            print(f"User {instance.email} added to Normal User group.")

    except Group.DoesNotExist as e:
        print(f"Group not found: {e}")
