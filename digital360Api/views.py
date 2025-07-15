import json
from tokenize import TokenError
from django.conf import settings
from django.utils import timezone
import random
from django.db import IntegrityError
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from nss_admin.models import Administrator
from nss_personnel.models import NSSPersonnel
from nss_personnel.serializer import NSSPersonnelSerializer
from nss_supervisors.models import Supervisor
from nss_supervisors.serializers import SupervisorSerializer

from .models import  MyUser, OTPVerification, Region,  UniversityRecord, GhanaCardRecord
from digital360Api.serializers import  GhanaCardRecordSerializer, OTPVerifySerializer, RegionSerializer,  UniversityRecordSerializer, UserSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, RegionalOverviewSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from file_uploads.models import UploadPDF
from evaluations.models import Evaluation
from .serializers import WorkplaceSerializer
from .models import Workplace
from .services import detect_ghost_personnel, detect_ghost_personnel_during_submission, calculate_severity, send_ghost_alert_to_admin
from .models import GhostDetection
from .serializers import GhostDetectionSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import traceback


@api_view(['GET'])
def index(request):
    return Response({'message': 'Setup was successful'})

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get('email')
    
    if MyUser.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            user.is_active = False 
            user.save()

            return Response({
                'message': 'Account created successfully! Check your email for OTP verification.',
                 "id": user.id, 
                'user': serializer.data,
            }, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({'error': 'An error occurred while creating the user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    API Endpoint to verify OTP and activate user.
    """
    serializer = OTPVerifySerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        try:
            user = get_user_model().objects.get(email=email)
            user_otp = OTPVerification.objects.filter(user=user).last()
            
            if not user_otp:
                return Response({'error': 'OTP not found!'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP has already been used
            if user_otp.is_used:
                return Response({'error': 'This OTP has already been used!'}, status=status.HTTP_400_BAD_REQUEST)
                
            # Check if OTP is valid
            if user_otp.otp_code == otp_code:
                if user_otp.expires_at > timezone.now():
                    # Mark OTP as used
                    user_otp.is_used = True
                    user_otp.save()
                    
                    # Activate user
                    user.is_active = True
                    user.save()
                    
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'message': 'Account activated successfully! You can now log in.',
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user': {'id': user.id, 'email': user.email}
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'The OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Invalid OTP entered. Please enter a valid OTP!'}, status=status.HTTP_400_BAD_REQUEST)
        except get_user_model().DoesNotExist:
            return Response({'error': 'User not found!'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def generate_otp_code():
    return str(random.randint(100000, 999999))

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """
    API Endpoint to resend OTP to user's email.
    """
    email = request.data.get('email')

    try:
        user = get_user_model().objects.get(email=email)

        # Generate new OTP
        otp = OTPVerification.objects.create(
            user=user,
            otp_code=generate_otp_code(),  # Generates a new OTP
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )

        # Email content
        subject = "Email Verification"
        message = f"""
            Hi {user.username}, here is your OTP: {otp.otp_code}
            It expires in 5 minutes. Use the link below to verify your email:
            http://127.0.0.1:8000/verify-email/{user.username}
        """
        sender_email = "clintonmatics@gmail.com"
        recipient_list = [user.email]

        # Send email
        send_mail(
            subject,
            message,
            sender_email,
            recipient_list,
            fail_silently=False,
        )

        return Response({'message': 'A new OTP has been sent to your email', 'email': user.email}, status=status.HTTP_200_OK)

    except get_user_model().DoesNotExist:
        return Response({'error': "This email doesn't exist in the database"}, status=status.HTTP_404_NOT_FOUND)
    

# GhanaCardRecord
@api_view(['POST'])
def ghanaCardRecords(request):
    data = request.data
    serializer = GhanaCardRecordSerializer(data = data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                'message': 'Data saved successfully',
                'id': serializer.instance.id,  # Send back the new ID
            }, status = status.HTTP_201_CREATED
        )
    else:
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
    
# Get all GhanaCardRecords
@api_view(['GET'])
def get_all_GhanaCardRecords(request):
    ghanacards = GhanaCardRecord.objects.all() 
    serializer = GhanaCardRecordSerializer(ghanacards, many=True)
    return Response(serializer.data)

# Count all GhanaCardRecords 
@api_view(['GET'])
def count_ghanaCardRecords(request):
    return Response({'count': GhanaCardRecord.objects.all().count()})

# UniversityDatabase
@api_view(['POST'])
def universityDatabase(request):
    data = request.data
    serializer = UniversityRecordSerializer(data = data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Data saved successfully'}, status = status.HTTP_201_CREATED
        )
    else:
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

# Get all GhanaCardRecords
@api_view(['GET'])
def get_all_universityDatabase(request):
    university = UniversityRecord.objects.all() 
    serializer = GhanaCardRecordSerializer(university, many=True)
    return Response(serializer.data)

# Count all GhanaCardRecords
@api_view(['GET'])
def count_universityDatabase(request):
    return Response({'count': UniversityRecord.objects.all().count()})


# Login using email and password endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    print('Request Data:', request.data)
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email and Password are required'}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(email=email, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        full_name = 'Unknown'

        try:
            
            nss_personnel = user.nss_profile  
            full_name = nss_personnel.full_name if nss_personnel.full_name else full_name

        
        except NSSPersonnel.DoesNotExist:
             pass
        try:
            if full_name == 'Unknown':
                admin = user.administrator_profile  
                full_name = admin.full_name if admin.full_name else full_name
        except Administrator.DoesNotExist:
            pass  # admin

        try:
            # Check for Supervisor profile if full_name is still 'Unknown'
            if full_name == 'Unknown':
                supervisor = user.supervisor_profile  
                full_name = supervisor.full_name if supervisor.full_name else full_name
        except Supervisor.DoesNotExist:
            pass  # supervisor_profile doesn't exist, so fall back to default

        if user.is_superuser:
            message = 'Admin Dashboard'   
            role = 'admin'
        elif user.is_staff:
            message = 'Supervisor Dashboard'
            role = 'supervisor'
        else:
            message = 'User Dashboard'
            role = 'user'

        return Response({
            'message': f'Login successful! Welcome to {message}',
            'refresh': str(refresh),
            'access': access_token,
            'user': { 
                'id': user.id,
                'email': user.email,
                'role': role,  
                'full_name': full_name,
                'permissions': {
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active
                }
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials. Please check your email and password.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except TokenError:
        # Handle expired token
        return Response({'message': 'Token is invalid or expired but user logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        # Log the error but still return a success response
        print(f"Error during logout: {str(e)}")
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

def get_user_permissions(user):
    return {
        'is_superuser': user.is_superuser, 
        'is_staff': user.is_staff, 
        'is_active': user.is_active
        }    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied. Admin privileges required.'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'message': 'Admin Dashboard'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supervisor_dashboard(request):
    if not request.user.is_staff:
        return Response({'error': 'Access denied. Supervisor privileges required.'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'message': 'Supervisor Dashboard'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    return Response({'message': 'User Dashboard'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def regions(request):
    serializer = RegionSerializer(Region.objects.all(), many=True)
    return Response(serializer.data)

# endpoint to return all nssmembers 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nssmembers(request):
    normal_users = MyUser.objects.filter(is_superuser=False, is_staff=False)
    serializer = UserSerializer(normal_users, many=True)
    return Response(serializer.data)

# Endpoint to return all supervisors
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supervisors(request):
    supervisors = MyUser.objects.filter(is_staff=True, is_superuser=False)
    serializer = UserSerializer(supervisors, many=True)
    return Response(serializer.data)

# Endpoint to return all admins
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admins(request):
    admins = MyUser.objects.filter(is_superuser=True)
    serializer = UserSerializer(admins, many=True)
    return Response(serializer.data)



# Count toatl users, admin and supervisors
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def user_counts(request):
    total_users = MyUser.objects.count()
    total_admins = MyUser.objects.filter(is_superuser=True).count()
    total_supervisors = MyUser.objects.filter(is_staff=True, is_superuser=False).count()
    total_normal_users = MyUser.objects.filter(is_superuser=False, is_staff=False).count()

    return Response({
        'total_users': total_users,
        'total_admins': total_admins,
        'total_supervisors': total_supervisors,
        'total_normal_users': total_normal_users
    }, status=status.HTTP_200_OK)


# End point to assign supervisors and nss members by admin



# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_superuser

# Get available supervisors for admin to assign
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_supervisors(request):
    if not is_admin(request.user):
        return Response({'error': 'Access denied. Admin privileges required.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        admin = Administrator.objects.get(user=request.user)
        supervisors = admin.assigned_supervisors.all()
        serializer = SupervisorSerializer(supervisors, many=True)
        return Response(serializer.data)
    except Administrator.DoesNotExist:
        return Response({'error': 'Administrator profile not found'}, 
                       status=status.HTTP_400_BAD_REQUEST)

# Assign supervisor to NSS personnel
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_supervisor(request, nss_id):
    if not is_admin(request.user):
        return Response({'error': 'Access denied. Admin privileges required.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        nss_personnel = NSSPersonnel.objects.get(id=nss_id)
    except NSSPersonnel.DoesNotExist:
        return Response({'error': 'NSS personnel not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Get supervisor ID from request data
    supervisor_id = request.data.get('supervisor_id')
    if not supervisor_id:
        return Response({'error': 'Supervisor ID is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        supervisor = Supervisor.objects.get(id=supervisor_id)
    except Supervisor.DoesNotExist:
        return Response({'error': 'Supervisor not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Check if the supervisor is assigned to this admin
    try:
        admin = Administrator.objects.get(user=request.user)
        if supervisor not in admin.assigned_supervisors.all():
            return Response({'error': 'You can only assign supervisors that are assigned to you'}, 
                           status=status.HTTP_403_FORBIDDEN)
    except Administrator.DoesNotExist:
        return Response({'error': 'Administrator profile not found'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Assign supervisor to NSS personnel
    nss_personnel.assigned_supervisor = supervisor
    nss_personnel.save()
    
    return Response({'success': 'Supervisor assigned successfully'}, 
                   status=status.HTTP_200_OK)

# Get NSS personnel assigned to a supervisor# Get NSS personnel assigned to a supervisor
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nss_by_supervisor(request, supervisor_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({'error': 'Access denied. Supervisor or admin privileges required.'}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    try:
        supervisor = Supervisor.objects.get(id=supervisor_id)
    except Supervisor.DoesNotExist:
        return Response({'error': 'Supervisor not found'}, 
                        status=status.HTTP_404_NOT_FOUND)
    
    # If user is a supervisor, they should only see their own NSS personnel
    if request.user.is_staff and not request.user.is_superuser:
        if not hasattr(request.user, 'supervisor_profile') or request.user.supervisor_profile != supervisor:
            return Response({'error': 'You can only view NSS personnel assigned to you'}, 
                            status=status.HTTP_403_FORBIDDEN)
    
    # 👉 FIX IS HERE
    nss_personnel = NSSPersonnel.objects.filter(assigned_supervisor=supervisor)
    serializer = NSSPersonnelSerializer(nss_personnel, many=True)
    
    return Response(serializer.data)

# Get all unassigned NSS personnel (for admin)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unassigned_nss(request):
    if not is_admin(request.user):
        return Response({'error': 'Access denied. Admin privileges required.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
        # 👇 Fix here: use 'assigned_supervisor' not 'supervisor'
    unassigned_nss = NSSPersonnel.objects.filter(assigned_supervisor=None)
    serializer = NSSPersonnelSerializer(unassigned_nss, many=True)
    
    return Response(serializer.data)

# assign supervisors to an admin

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_supervisors_to_admin(request):
    if not is_admin(request.user):
        return Response({'error': 'Access denied. Admin privileges required.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    supervisor_ids = request.data.get('supervisor_ids', [])
    if not supervisor_ids:
        return Response({'error': 'Supervisor IDs are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        admin = Administrator.objects.get(user=request.user)
    except Administrator.DoesNotExist:
        return Response({'error': 'Administrator profile not found'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Get supervisors from provided IDs
    supervisors = Supervisor.objects.filter(id__in=supervisor_ids)
    if len(supervisors) != len(supervisor_ids):
        return Response({'error': 'One or more supervisor IDs are invalid'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Assign supervisors to admin
    admin.assigned_supervisors.add(*supervisors)
    
    return Response({'success': 'Supervisors assigned successfully to admin'}, 
                   status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password for authenticated user
    """
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']
        
        # Check if current password is correct
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Request password reset - sends OTP to user's email
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = get_user_model().objects.get(email=email)
            
            # Generate OTP for password reset
            otp_code = str(random.randint(100000, 999999))
            otp_expires_at = timezone.now() + timezone.timedelta(minutes=10)
            
            # Create OTP record
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                expires_at=otp_expires_at
            )
            
            # Send email with OTP
            subject = "Password Reset Request"
            message = f"""
            Hi {user.username},
            
            You requested a password reset. Here is your OTP: {otp_code}
            It expires in 10 minutes.
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            NSS Team
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                return Response({
                    'message': 'Password reset OTP sent to your email',
                    'email': user.email
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': 'Failed to send email. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except get_user_model().DoesNotExist:
            return Response({
                'error': 'No user found with this email address'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    """
    Confirm password reset with OTP and set new password
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = get_user_model().objects.get(email=email)
            user_otp = OTPVerification.objects.filter(user=user).last()
            
            if not user_otp:
                return Response({'error': 'OTP not found'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP has already been used
            if user_otp.is_used:
                return Response({'error': 'This OTP has already been used'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP is valid
            if user_otp.otp_code == otp_code:
                if user_otp.expires_at > timezone.now():
                    # Mark OTP as used
                    user_otp.is_used = True
                    user_otp.save()
                    
                    # Set new password
                    user.set_password(new_password)
                    user.save()
                    
                    return Response({
                        'message': 'Password reset successfully. You can now log in with your new password.'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'The OTP has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': 'Invalid OTP entered. Please enter a valid OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except get_user_model().DoesNotExist:
            return Response({
                'error': 'No user found with this email address'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_region_data(request):
    # Only allow admins
    user = request.user
    if getattr(user, 'user_type', None) != 'admin':
        return Response({'error': 'Only admins can access this endpoint'}, status=403)

    regions = Region.objects.all()
    data = []
    for region in regions:
        # Personnel in this region
        personnel_qs = NSSPersonnel.objects.filter(region_of_posting=region)
        total_personnel = personnel_qs.count()

        # Supervisors in this region
        supervisor_qs = Supervisor.objects.filter(assigned_region=region)
        supervisor_count = supervisor_qs.count()

        # Submissions (UploadPDF and Evaluation) for personnel in this region
        personnel_users = [p.user for p in personnel_qs if p.user]
        # UploadPDFs
        pdfs = UploadPDF.objects.filter(user__in=personnel_users)
        # Evaluations
        evals = Evaluation.objects.filter(nss_personnel__in=personnel_users)

        # Pending and completed submissions
        pending_submissions = pdfs.filter(status__in=['pending', 'under_review']).count() + evals.filter(status__in=['pending', 'under_review']).count()
        completed_submissions = pdfs.filter(status='approved').count() + evals.filter(status='approved').count()

        data.append({
            'region': region.name,
            'total_personnel': total_personnel,
            'pending_submissions': pending_submissions,
            'completed_submissions': completed_submissions,
            'supervisor_count': supervisor_count,
        })

    serializer = RegionalOverviewSerializer(data, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workplaces(request):
    """Return all workplaces for admin/supervisor assignment."""
    workplaces = Workplace.objects.all()
    serializer = WorkplaceSerializer(workplaces, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_ghost_dashboard(request):
    """
    Admin dashboard for managing ghost detections
    """
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    print(f"🔍 Admin ghost dashboard accessed by: {request.user.email}")
    
    # Get all ghost detections
    ghost_detections = GhostDetection.objects.all().select_related(
        'nss_personnel', 'supervisor', 'assigned_admin'
    )
    
    print(f"📊 Total ghost detections found: {ghost_detections.count()}")
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        ghost_detections = ghost_detections.filter(status=status_filter)
        print(f"🔍 Filtered by status '{status_filter}': {ghost_detections.count()} detections")
    
    # Filter by severity if provided
    severity_filter = request.GET.get('severity')
    if severity_filter:
        ghost_detections = ghost_detections.filter(severity=severity_filter)
        print(f"🔍 Filtered by severity '{severity_filter}': {ghost_detections.count()} detections")
    
    # Serialize the data
    try:
        serializer = GhostDetectionSerializer(ghost_detections, many=True)
        serialized_data = serializer.data
        print(f"✅ Serialized {len(serialized_data)} detections successfully")
        
        # Debug: Print first detection if any
        if serialized_data:
            print(f"📋 First detection: {serialized_data[0]}")
        
    except Exception as e:
        print(f"❌ Serialization error: {str(e)}")
        return Response({'error': f'Serialization error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Calculate statistics
    total_detections = ghost_detections.count()
    pending_count = ghost_detections.filter(status='pending').count()
    investigating_count = ghost_detections.filter(status='investigating').count()
    resolved_count = ghost_detections.filter(status='resolved').count()
    critical_count = ghost_detections.filter(severity='critical').count()
    high_count = ghost_detections.filter(severity='high').count()
    medium_count = ghost_detections.filter(severity='medium').count()
    low_count = ghost_detections.filter(severity='low').count()
    
    response_data = {
        'detections': serialized_data,
        'statistics': {
            'total_detections': total_detections,
            'pending_count': pending_count,
            'investigating_count': investigating_count,
            'resolved_count': resolved_count,
            'critical_count': critical_count,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count,
        }
    }
    
    print(f"📈 Statistics: {response_data['statistics']}")
    
    return Response(response_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_investigate_ghost(request, detection_id):
    """
    Admin investigation action
    """
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        detection = GhostDetection.objects.get(id=detection_id)
        admin = request.user.administrator_profile
        
        # Update status
        detection.status = 'investigating'
        detection.assigned_admin = admin
        detection.save()
        
        # Log admin action
        from nss_supervisors.models import ActivityLog
        ActivityLog.objects.create(
            supervisor=admin.user,
            action='admin_investigation_started',
            title=f"Admin Investigation: {detection.nss_personnel.full_name}",
            description=f"Admin {admin.full_name} started investigation",
            personnel=detection.nss_personnel.full_name,
            priority='high'
        )
        
        return Response({'status': 'investigation_started'})
    except GhostDetection.DoesNotExist:
        return Response({'error': 'Detection not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_resolve_ghost(request, detection_id):
    """
    Admin resolution action
    """
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        detection = GhostDetection.objects.get(id=detection_id)
        admin = request.user.administrator_profile
        
        resolution_type = request.data.get('resolution_type')
        action_taken = request.data.get('action_taken')
        notes = request.data.get('notes')
        
        detection.status = resolution_type
        detection.resolved_at = timezone.now()
        detection.admin_action_taken = action_taken
        detection.resolution_notes = notes
        detection.assigned_admin = admin
        detection.save()
        
        # Notify supervisor of resolution
        from messageApp.models import Message
        Message.objects.create(
            sender=admin.user,
            receiver=detection.supervisor.user,
            subject=f"Ghost Detection Resolved: {detection.nss_personnel.full_name}",
            content=f"""
            Ghost detection investigation completed:
            
            Personnel: {detection.nss_personnel.full_name}
            Resolution: {resolution_type}
            Action Taken: {action_taken}
            Notes: {notes}
            
            Admin: {admin.full_name}
            """,
            priority='medium',
            message_type='report'
        )
        
        return Response({'status': 'resolved'})
    except GhostDetection.DoesNotExist:
        return Response({'error': 'Detection not found'}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_ghost_detection(request):
    """
    Test endpoint for ghost detection during evaluation submission
    This simulates the ghost detection process for the frontend
    """
    personnel_id = request.data.get('personnel_id')
    print(f"[DEBUG] Incoming test_ghost_detection request with personnel_id: {personnel_id}")
    
    if not personnel_id:
        print("[ERROR] No personnel_id provided in request data.")
        return Response({'error': 'Personnel ID is required'}, status=400)
    
    try:
        # Run ghost detection
        ghost_result = detect_ghost_personnel(personnel_id)
        print(f"[DEBUG] Ghost detection result: {ghost_result}")
        
        if ghost_result['is_ghost']:
            # Create a GhostDetection record
            try:
                personnel = NSSPersonnel.objects.get(id=personnel_id)
                supervisor = personnel.assigned_supervisor
                # Use the first admin as assigned_admin (or None if not available)
                from nss_admin.models import Administrator
                admin = Administrator.objects.first()
                detection = GhostDetection.objects.create(
                    nss_personnel=personnel,
                    supervisor=supervisor,
                    assigned_admin=admin,
                    detection_flags=ghost_result['flags'],
                    severity=ghost_result['severity'],
                    status='pending',
                    submission_attempt=True
                )
                print(f"[DEBUG] Created GhostDetection record: {detection}")
            except Exception as db_exc:
                print(f"[ERROR] Could not create GhostDetection record: {db_exc}")
            return Response({
                'status': 'ghost_detected',
                'message': 'Ghost personnel detected during security verification',
                'details': ghost_result
            }, status=200)
        else:
            return Response({
                'status': 'clean',
                'message': 'Security verification passed',
                'details': ghost_result
            }, status=200)
            
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] Exception in test_ghost_detection: {e}\n{tb}")
        return Response({
            'status': 'error',
            'message': f'Error during ghost detection: {str(e)}',
            'traceback': tb
        }, status=500)
