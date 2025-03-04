from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import MyUser, Region

@receiver(post_save, sender=MyUser)
def update_user_role(sender, instance, created, **kwargs):
    """
    Signal that listens for changes in user roles and updates them accordingly.
    """
    if created:
        # We want this to run on user creation now
        group_name = "Admin" if instance.is_superuser else (
            "Supervisor" if instance.is_staff else "Normal User"
        )
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
        print(f"User {instance.email} added to {group_name} group.")

@receiver(post_migrate)
def populate_regions(sender, **kwargs):
    """
    Populate regions based on the GHANA_REGIONS choices defined in the Region model.
    """
    if sender.name == 'digital360Api':  # Replace with your actual app name
        for region_code, region_name in Region.GHANA_REGIONS:
            Region.objects.get_or_create(name=region_code)
        print("Regions populated successfully")