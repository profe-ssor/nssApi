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
from digital360Api.models import MyUser, OTPVerification, Region, UploadPDF
from digital360Api.serializers import OTPVerifySerializer, RegionSerializer, UserSerializer, UploadPDFSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.contrib.auth import authenticate
import fitz
import base64
import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
# Create your views here.

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
            'user': {  # Include user data here
                'email': user.email,
                'role': role,  # Add role to the response
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
        'is_staff': user.is_staff, ''
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
    serializer = UserSerializer(nssmembers, many=True)
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

# Endpoint to upload pdf


# Make sure the directory exists
os.makedirs(os.path.join(settings.MEDIA_ROOT, 'signed_docs'), exist_ok=True)

def apply_signature(pdf_instance, signature_bytes, position=None):
    """
    Apply signature to PDF and save the result
    
    Args:
        pdf_instance: UploadPDF model instance
        signature_bytes: Image bytes of the signature
        position: Dict with x, y, width, height (optional)
    
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Create temporary signature file
        temp_signature = BytesIO(signature_bytes)
        
        # Open PDF
        pdf_path = pdf_instance.file.path
        doc = fitz.open(pdf_path)
        
        if not doc.page_count:
            return False, "PDF has no pages"
        
        # Use first page by default
        page = doc[0]
        
        # Calculate signature position (default or custom)
        if position:
            signature_rect = fitz.Rect(
                position.get('x', 100),
                position.get('y', 100),
                position.get('x', 100) + position.get('width', 200),
                position.get('y', 100) + position.get('height', 100)
            )
        else:
            # Default position - bottom right of the page
            page_rect = page.rect
            signature_rect = fitz.Rect(
                page_rect.width - 300,
                page_rect.height - 150,
                page_rect.width - 100,
                page_rect.height - 50
            )
        
        # Insert signature
        page.insert_image(signature_rect, stream=temp_signature)
        
        # Save signed PDF
        signed_filename = f"signed_{os.path.basename(pdf_instance.file.name)}"
        signed_path = os.path.join(settings.MEDIA_ROOT, 'signed_docs', signed_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(signed_path), exist_ok=True)
        
        # Save the document
        doc.save(signed_path)
        doc.close()
        
        # Update model
        pdf_instance.is_signed = True
        with open(signed_path, 'rb') as f:
            pdf_instance.signed_file.save(signed_filename, ContentFile(f.read()), save=False)
        pdf_instance.save()
        
        return True, None
    except Exception as e:
        return False, str(e)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_pdf(request):
    """Upload a new PDF document"""
    pdf_file = request.FILES.get('pdf')
    if not pdf_file:
        return Response({"error": "PDF file is required."}, status=400)
    
    # Validate PDF file
    if not pdf_file.name.lower().endswith('.pdf'):
        return Response({"error": "File must be a PDF."}, status=400)
    
    # Create new PDF upload
    upload = UploadPDF.objects.create(
        user=request.user,
        file_name=request.data.get('file_name', os.path.splitext(pdf_file.name)[0]),
        file=pdf_file
    )
    
    serializer = UploadPDFSerializer(upload)
    
    return Response({
        "message": "PDF uploaded successfully!",
        "data": serializer.data
    }, status=201)


@api_view(['GET'])

def list_pdfs(request):
    """List all PDFs uploaded by the user"""
    pdfs = UploadPDF.objects.filter()
    serializer = UploadPDFSerializer(pdfs, many=True)
    return Response(serializer.data)

@api_view(['GET'])

def get_pdf(request, pk):
    """Get details of a specific PDF"""
    try:
        pdf = UploadPDF.objects.get(pk=pk, user=request.user)
    except UploadPDF.DoesNotExist:
        return Response({"error": "PDF not found"}, status=404)
    
    serializer = UploadPDFSerializer(pdf)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_with_drawing(request, pk):
    """Sign a PDF with a drawing (base64 encoded data)"""
    try:
        pdf = UploadPDF.objects.get(pk=pk, user=request.user)
    except UploadPDF.DoesNotExist:
        return Response({"error": "PDF not found"}, status=404)

    signature_data = request.data.get('signature')
    if not signature_data:
        return Response({"error": "Signature data is required"}, status=400)

    # Get position data if provided
    position = request.data.get('position')
    if position and not isinstance(position, dict):
        try:
            position = eval(position)  # Convert string to dict if needed
        except:
            position = None

    try:
        # Extract base64 data
        if ',' in signature_data:
            signature_data = signature_data.split(',')[1]
        
        # Decode base64 data
        decoded_data = base64.b64decode(signature_data)
        
        # Verify and convert to image
        img = Image.open(BytesIO(decoded_data))
        
        # Convert to PNG bytes
        png_bytes = BytesIO()
        img.save(png_bytes, format='PNG')
        png_bytes.seek(0)
        
        # Save drawing data
        pdf.signature_drawing = signature_data
        
        # Apply signature
        success, error = apply_signature(pdf, png_bytes.getvalue(), position)
        if not success:
            return Response({"error": error}, status=500)
        
        serializer = UploadPDFSerializer(pdf)
        return Response({
            "message": "PDF signed with drawing successfully!",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return Response({"error": f"Invalid signature data: {str(e)}"}, status=400)
