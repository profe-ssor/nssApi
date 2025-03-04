from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .models import MyUser, Region
from .serializers import RegionSerializer, UserSerializer
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated 
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.models import User

# Test the api see if it works properly by displaying Setup was successful
@api_view(['GET'])
def index(request):
    return Response({'message': 'Setup was successful'})


# Registrations  endpoints
@api_view(['POST'])
def register(request):
    print('Request Data:', request.data)
    email = request.data.get('email')

    # Check if email already exists
    if MyUser.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    # Create a new user with the validated data
    serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        try:
            user = serializer.save()  # Save the user
            refresh = RefreshToken.for_user(user)  # Generate tokens
            access_token = str(refresh.access_token)
            
            messages.success(request, 'Registration successful! Welcome to NSS Portal.')

            return Response({
                'message': 'Registration successful! Welcome to NSS Portal.',
                'user': serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': access_token,
                },
            }, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            print(f"IntegrityError while creating user: {str(e)}")  
            return Response({'error': 'An error occurred while creating the user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        print(f"Validation errors: {serializer.errors}")  # Log validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

# Login using email and password endpoints
@api_view(['POST'])
def login(request):
    print('Request Data:', request.data)
    email = request.data.get('email')
    password = request.data.get('password')

    # Check if email and password are provided
    if not email or not password:
        return Response({'error': 'Email and Password are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Authenticate the user
    user = authenticate(email=email, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Determine the user's role and message
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

    
# get user by permission
def get_user_permissions(user):
    """Get user permissions"""
    return {
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'is_active': user.is_active
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if not request.user.is_superuser:
        return Response({
            'error': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'message': 'Admin Dashboard',
        'data': {
            # Add admin-specific data here
        }
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supervisor_dashboard(request):
    if not request.user.is_staff:
        return Response({
            'error': 'Access denied. Supervisor privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'message': 'Supervisor Dashboard',
        'data': {
            # Add supervisor-specific data here
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    return Response({
        'message': 'User Dashboard',
        'data': {
            # Add user-specific data here
        }
    }) 
# Logout endpoint
@api_view(['POST'])
def logout(request):
    print('Request Data:', request.data)
    refresh_token = request.data.get('refresh_token')

    # Check if refresh token is valid
    try:
        refresh_token_obj = RefreshToken(refresh_token)
        refresh_token_obj.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error while blacklisting token: {str(e)}")
        return Response({'error': 'An error occurred while logging out'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Regions endpoint
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def regions(request):
    regions = Region.objects.all()
    serializer = RegionSerializer(regions, many=True)
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
@permission_classes([IsAuthenticated])
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
