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
from digital360Api.serializers import  GhanaCardRecordSerializer, OTPVerifySerializer, RegionSerializer,  UniversityRecordSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.contrib.auth import authenticate


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
