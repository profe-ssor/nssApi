from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import random
import logging
from .models import MyUser, OTPVerification, UploadPDF
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group




logger = logging.getLogger(__name__)

@receiver(post_save, sender=MyUser)
def update_user_role_and_create_otp(sender, instance, created, **kwargs):
    if created:
        try:
            # Generate OTP
            otp_code = str(random.randint(100000, 999999))
            otp_expires_at = timezone.now() + timezone.timedelta(minutes=5)
            OTPVerification.objects.create(
                user=instance,
                otp_code=otp_code,
                expires_at=otp_expires_at
            )
            instance.is_active = False
            instance.save()
            
            # Send email with better error handling
            try:
                send_mail(
                    subject="Email Verification",
                    message=f"Hi {instance.username}, here is your OTP {otp_code} \n"
                            f"it expires in 5 minutes, use the url below to redirect back to the website \n"
                            f"http://127.0.0.1:8000/verify-email/{instance.username}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
                print(f"OTP sent successfully to {instance.email}")
            except Exception as e:
                logger.error(f"Failed to send OTP email to {instance.email}: {str(e)}")
                print(f"SMTP Error details: {e}")
        except Exception as e:
            logger.error(f"Error in OTP creation process: {str(e)}")



