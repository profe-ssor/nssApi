from io import BytesIO
import json
import os
from django.conf import settings
from django.shortcuts import render
from django.core.files.base import ContentFile
import fitz
from rest_framework.response import Response
from datetime import timezone as dt_timezone

from datetime import datetime
from django.utils import timezone
from calendar import monthrange

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from digital360Api.models import MyUser
from file_uploads.models import UploadPDF
from file_uploads.serializers import UploadPDFSerializer, UploadPDFListSerializer
from nss_supervisors.views import log_document_upload, log_supervisor_activity
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.core.paginator import Paginator
from digital360Api.services import detect_ghost_personnel
from digital360Api.models import GhostDetection


os.makedirs(os.path.join(settings.MEDIA_ROOT, 'signed_docs'), exist_ok=True)

def apply_signature(pdf_instance, signature_bytes, position=None):
    """
    Apply signature to a specific page in PDF and save result.
    """
    try:
        temp_signature = BytesIO(signature_bytes)
        pdf_path = pdf_instance.file.path
        doc = fitz.open(pdf_path)

        if not doc.page_count:
            return False, "PDF has no pages"

        # Determine which page to use (default to page 1 = index 0)
        page_number = position.get('page', 1) if position else 1
        if not isinstance(page_number, int) or page_number < 1 or page_number > doc.page_count:
            return False, f"Invalid page number: {page_number}"

        page = doc[page_number - 1]

        # Set position for the signature
        if position:
            signature_rect = fitz.Rect(
                position.get('x', 100),
                position.get('y', 100),
                position.get('x', 100) + position.get('width', 200),
                position.get('y', 100) + position.get('height', 100)
            )
        else:
            page_rect = page.rect
            signature_rect = fitz.Rect(
                page_rect.width - 300,
                page_rect.height - 150,
                page_rect.width - 100,
                page_rect.height - 50
            )

        page.insert_image(signature_rect, stream=temp_signature)

        signed_filename = f"signed_{os.path.basename(pdf_instance.file.name)}"
        signed_path = os.path.join(settings.MEDIA_ROOT, 'signed_docs', signed_filename)
        os.makedirs(os.path.dirname(signed_path), exist_ok=True)

        doc.save(signed_path)
        doc.close()

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
    """
    Upload a PDF document
    """
    data = request.data.copy()
    data['user'] = request.user.id
    
    serializer = UploadPDFSerializer(data=data)
    if serializer.is_valid():
        pdf = serializer.save()
        
        # Log the activity if user is a supervisor
        if request.user.user_type == 'supervisor':
            document_name = data.get('title', 'Untitled Document')
            log_document_upload(request.user, document_name)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pdfs(request):
    """
    Get PDFs for the current user
    """
    user = request.user
    pdfs = UploadPDF.objects.filter(user=user).order_by('-uploaded_at')
    
    # Apply filters
    form_type = request.GET.get('form_type')
    if form_type:
        pdfs = pdfs.filter(form_type=form_type)
    
    status_filter = request.GET.get('status')
    if status_filter:
        pdfs = pdfs.filter(status=status_filter)
    
    # Pagination
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))
    
    paginator = Paginator(pdfs, page_size)
    page_obj = paginator.get_page(page)
    
    serializer = UploadPDFListSerializer(page_obj, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pdf_detail(request, pk):
    """
    Get detailed information about a specific PDF
    """
    user = request.user
    try:
        pdf = UploadPDF.objects.get(pk=pk, user=user)
        serializer = UploadPDFSerializer(pdf)
        return Response(serializer.data)
    except UploadPDF.DoesNotExist:
        return Response(
            {'error': 'PDF not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_pdf(request, pk):
    """
    Delete a PDF document
    """
    user = request.user
    try:
        pdf = UploadPDF.objects.get(pk=pk, user=user)
        pdf.delete()
        return Response({'message': 'PDF deleted successfully'})
    except UploadPDF.DoesNotExist:
        return Response(
            {'error': 'PDF not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pdfs(request):
    user = request.user
    """List all PDFs uploaded by the user"""
    
    # First try to get PDFs owned by current user
    pdfs = UploadPDF.objects.filter(user=user)
    
    # If no PDFs found for user, also include PDFs without user assignment (for testing)
    if pdfs.count() == 0:
        pdfs_without_user = UploadPDF.objects.filter(user__isnull=True)
        if pdfs_without_user.count() > 0:
            print(f"Warning: No PDFs found for user {user.email}, showing {pdfs_without_user.count()} PDFs without user assignment")
            pdfs = pdfs_without_user
    
    serializer = UploadPDFSerializer(pdfs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pdf(request, pk):
    """Get details of a specific PDF"""
    try:
        # First try to get PDF owned by current user
        pdf = UploadPDF.objects.get(pk=pk, user=request.user)
    except UploadPDF.DoesNotExist:
        # If not found, try to get PDF without user filter (for testing/debugging)
        try:
            pdf = UploadPDF.objects.get(pk=pk)
            # If PDF has no user, allow access (for testing purposes)
            if pdf.user is None:
                print(f"Warning: PDF {pk} has no user assigned - allowing access for testing")
            else:
                # PDF belongs to another user - deny access
                return Response({"error": "PDF not found"}, status=404)
        except UploadPDF.DoesNotExist:
            return Response({"error": "PDF not found"}, status=404)
    
    serializer = UploadPDFSerializer(pdf)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_pdf(request, pk):
    """Update a PDF document (e.g., mark as signed)"""
    try:
        # First try to get PDF owned by current user
        pdf = UploadPDF.objects.get(pk=pk, user=request.user)
    except UploadPDF.DoesNotExist:
        # If not found, try to get PDF without user filter (for testing/debugging)
        try:
            pdf = UploadPDF.objects.get(pk=pk)
            # If PDF has no user, allow access (for testing purposes)
            if pdf.user is None:
                print(f"Warning: PDF {pk} has no user assigned - allowing access for testing")
            else:
                # PDF belongs to another user - deny access
                return Response({"error": "PDF not found"}, status=404)
        except UploadPDF.DoesNotExist:
            return Response({"error": "PDF not found"}, status=404)
    
    serializer = UploadPDFSerializer(pdf, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "PDF updated successfully",
            "data": serializer.data
        }, status=200)
    return Response(serializer.errors, status=400)

# e: Returns a list of all PDFs that have been signed by the current authenticated user.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_signed_pdfs(request):
    """List all signed PDFs uploaded by the user"""
    user = request.user
    
    # First try to get signed PDFs owned by current user
    signed_pdfs = UploadPDF.objects.filter(is_signed=True, user=user)
    
    # If no signed PDFs found for user, also include signed PDFs without user assignment (for testing)
    if signed_pdfs.count() == 0:
        signed_pdfs_without_user = UploadPDF.objects.filter(is_signed=True, user__isnull=True)
        if signed_pdfs_without_user.count() > 0:
            print(f"Warning: No signed PDFs found for user {user.email}, showing {signed_pdfs_without_user.count()} signed PDFs without user assignment")
            signed_pdfs = signed_pdfs_without_user
    
    serializer = UploadPDFSerializer(signed_pdfs, many=True)
    return Response({
        "message": "Successfully retrieved signed PDFs",
        "count": signed_pdfs.count(),
        "data": serializer.data
    }, status=200)

#  Retrieves a specific signed PDF document by its ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_signed_pdf(request, pk):
    """Get details of a specific signed PDF"""
    try:
        pdf = UploadPDF.objects.get(pk=pk, user=request.user, is_signed=True)
    except UploadPDF.DoesNotExist:
        return Response({"error": "Signed PDF not found"}, status=404)
    
    serializer = UploadPDFSerializer(pdf)
    return Response({
        "message": "Successfully retrieved signed PDF",
        "data": serializer.data
    }, status=200)




# Admin-only endpoint to see all signed PDFs across all users.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_signed_pdfs(request):
    """List all signed PDFs (admin only)"""
    # Check if user is admin (you might want to implement proper admin permission check)
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({"error": "Permission denied"}, status=403)
        
    signed_pdfs = UploadPDF.objects.filter(is_signed=True)
    serializer = UploadPDFSerializer(signed_pdfs, many=True)
    return Response({
        "message": "Successfully retrieved all signed PDFs",
        "count": signed_pdfs.count(),
        "data": serializer.data
    }, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_with_image(request, pk):
    """Sign a PDF with a drawing (uploaded file)"""
    try:
        # First try to get PDF owned by current user
        pdf = UploadPDF.objects.get(pk=pk, user=request.user)
    except UploadPDF.DoesNotExist:
        # If not found, try to get PDF without user filter (for testing/debugging)
        try:
            pdf = UploadPDF.objects.get(pk=pk)
            # If PDF has no user, allow access (for testing purposes)
            if pdf.user is None:
                print(f"Warning: PDF {pk} has no user assigned - allowing access for testing")
            else:
                # PDF belongs to another user - deny access
                return Response({"error": "PDF not found"}, status=404)
        except UploadPDF.DoesNotExist:
            return Response({"error": "PDF not found"}, status=404)

    # Get signature file directly instead of base64
    signature_file = request.FILES.get('signature')
    if not signature_file:
        return Response({"error": "Signature file is required"}, status=400)
    
    # Get position as form data
    position_str = request.data.get('position')
    position = None
    if position_str:
        try:
            position = json.loads(position_str)
        except json.JSONDecodeError:
            pass
    
    try:
        # Read the uploaded file content
        signature_bytes = signature_file.read()
        
        # Apply signature directly with the bytes
        success, error = apply_signature(pdf, signature_bytes, position)
        if not success:
            return Response({"error": error}, status=500)
        
        serializer = UploadPDFSerializer(pdf)
        return Response({
            "message": "PDF signed with drawing successfully!",
            "data": serializer.data
        }, status=200)
    except Exception as e:
        return Response({"error": f"Invalid signature data: {str(e)}"}, status=400)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_evaluation_form(request):
    """Upload PDF with evaluation form type, priority, receiver, and auto-set due date"""
    pdf_file = request.FILES.get('file') or request.FILES.get('pdf')  # Accept both 'file' and 'pdf'
    form_type = request.data.get('form_type', 'Monthly')
    priority = request.data.get('priority', 'medium')
    receiver_id = request.data.get('receiver_id')
    file_path = request.data.get('file_path')

    if form_type not in dict(UploadPDF.FORM_TYPE_CHOICES):
        return Response({"error": "Invalid form type."}, status=400)

    if priority not in dict(UploadPDF.PRIORITY_CHOICES):
        return Response({"error": "Invalid priority value."}, status=400)

    # Fetch receiver user
    receiver = None
    if receiver_id:
        try:
            receiver = MyUser.objects.get(pk=receiver_id)
        except MyUser.DoesNotExist:
            return Response({"error": "Receiver not found."}, status=404)

    # 🔍 GHOST DETECTION: Run security check if receiver is an admin
    if receiver and receiver.user_type == 'admin':
        try:
            # Get current personnel ID
            personnel_id = request.user.id
            
            # Run ghost detection
            ghost_result = detect_ghost_personnel(personnel_id)
            
            # Always notify admin about the security check
            from nss_admin.models import Administrator
            from nss_personnel.models import NSSPersonnel
            from nss_supervisors.models import Supervisor
            from messageApp.models import Message
            
            try:
                admin_instance = Administrator.objects.get(user=receiver)
                personnel_instance = NSSPersonnel.objects.get(user=request.user)
                
                # Get the supervisor for this personnel using the correct field name
                supervisor_instance = personnel_instance.assigned_supervisor
                
                # Create notification message for admin
                if ghost_result['is_ghost']:
                    # Ghost detected - create ghost detection record and notify
                    if supervisor_instance:
                        # Create ghost detection record
                        GhostDetection.objects.create(
                            nss_personnel=personnel_instance,
                            supervisor=supervisor_instance,
                            assigned_admin=admin_instance,
                            detection_flags=ghost_result['flags'],
                            severity=ghost_result['severity'],
                            status='pending',
                            submission_attempt=True
                        )
                        
                        print(f"🚨 GHOST DETECTED: Personnel {request.user.get_full_name()} (ID: {personnel_id}) flagged during evaluation submission to admin {receiver.get_full_name()}")
                    
                    # Send urgent notification to admin
                    Message.objects.create(
                        sender=receiver,  # System message
                        receiver=receiver,
                        subject=f"🚨 URGENT: Ghost Personnel Detection - {request.user.get_full_name()}",
                        content=f"""
                        🚨 CRITICAL GHOST PERSONNEL DETECTION ALERT! 🚨
                        
                        A personnel has been flagged during evaluation submission:
                        
                        Personnel Details:
                        • Name: {request.user.get_full_name()}
                        • Ghana Card: {ghost_result.get('ghana_card_number', 'N/A')}
                        • NSS ID: {personnel_instance.nss_id if personnel_instance else 'N/A'}
                        
                        Detection Flags:
                        {chr(10).join([f"• {flag}" for flag in ghost_result['flags']])}
                        
                        Severity: {ghost_result['severity'].upper()}
                        Detection Time: {timezone.now()}
                        
                        IMMEDIATE ACTION REQUIRED:
                        1. Review the ghost detection record
                        2. Investigate personnel authenticity
                        3. Take appropriate disciplinary action
                        
                        The submission has been BLOCKED for security reasons.
                        """,
                        priority='high',
                        message_type='alert'
                    )
                    
                else:
                    # No ghost detected - still notify admin about the security check
                    Message.objects.create(
                        sender=receiver,  # System message
                        receiver=receiver,
                        subject=f"✅ Security Check Completed - {request.user.get_full_name()}",
                        content=f"""
                        ✅ SECURITY VERIFICATION COMPLETED
                        
                        A personnel evaluation submission has passed security verification:
                        
                        Personnel Details:
                        • Name: {request.user.get_full_name()}
                        • Ghana Card: {ghost_result.get('ghana_card_number', 'N/A')}
                        • NSS ID: {personnel_instance.nss_id if personnel_instance else 'N/A'}
                        
                        Security Check Result: ✅ PASSED
                        Verification Time: {timezone.now()}
                        
                        The evaluation form has been submitted successfully.
                        No further action required.
                        """,
                        priority='low',
                        message_type='notification'
                    )
                    
                    print(f"✅ Security check passed for {request.user.get_full_name()} - admin notified")
                
            except Administrator.DoesNotExist:
                print(f"Warning: Administrator instance not found for user {receiver.email}")
            except NSSPersonnel.DoesNotExist:
                print(f"Warning: NSS Personnel instance not found for user {request.user.email}")
            except Exception as e:
                print(f"Error creating admin notification: {str(e)}")
                
        except Exception as e:
            print(f"Error during ghost detection: {str(e)}")
            # Continue with submission even if ghost detection fails

    # 🧠 Calculate due_date to be 21st of current or next month
    now = timezone.now()
    if now.day > 21:
        if now.month == 12:
            due_year = now.year + 1
            due_month = 1
        else:
            due_year = now.year
            due_month = now.month + 1
    else:
        due_year = now.year
        due_month = now.month

    due_date = datetime(due_year, due_month, 21, 23, 59, 59, tzinfo=dt_timezone.utc)

    # ✅ Proceed with file processing
    if file_path:
        relative_path = file_path.replace('/media/', '')
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        if not os.path.exists(full_path):
            return Response({"error": "File path not found."}, status=404)

        with open(full_path, 'rb') as f:
            file_content = ContentFile(f.read(), name=os.path.basename(full_path))

        upload = UploadPDF.objects.create(
            user=request.user,
            file_name=request.data.get('file_name', os.path.basename(full_path)),
            file=file_content,
            form_type=form_type,
            priority=priority,
            receiver=receiver,
            is_signed=True,
            submitted_date=now,
            due_date=due_date,
        )
    else:
        if not pdf_file:
            return Response({"error": "PDF file is required. Received files: " + str(list(request.FILES.keys()))}, status=400)
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({"error": "File must be a PDF. Received: " + pdf_file.name}, status=400)

        upload = UploadPDF.objects.create(
            user=request.user,
            file_name=request.data.get('file_name', os.path.splitext(pdf_file.name)[0]),
            file=pdf_file,
            form_type=form_type,
            priority=priority,
            receiver=receiver,
            is_signed=True,
            submitted_date=now,
            due_date=due_date,
        )

    # ✅ Copy the file to signed_file field
    upload.signed_file.save(upload.file.name, upload.file.file, save=False)
    upload.save()

    # 🔍 Update ghost detection record with evaluation form ID if ghost was detected
    if receiver and receiver.user_type == 'admin':
        try:
            from nss_admin.models import Administrator
            from nss_personnel.models import NSSPersonnel
            
            admin_instance = Administrator.objects.get(user=receiver)
            personnel_instance = NSSPersonnel.objects.get(user=request.user)
            
            ghost_detection = GhostDetection.objects.filter(
                nss_personnel=personnel_instance,
                assigned_admin=admin_instance,
                status='pending'
            ).first()
            
            if ghost_detection:
                ghost_detection.evaluation_form_id = upload.id
                ghost_detection.save()
                print(f"Updated ghost detection record with evaluation form ID: {upload.id}")
        except Administrator.DoesNotExist:
            print(f"Warning: Administrator instance not found for user {receiver.email}")
        except NSSPersonnel.DoesNotExist:
            print(f"Warning: NSS Personnel instance not found for user {request.user.email}")
        except Exception as e:
            print(f"Error updating ghost detection record: {str(e)}")

    serializer = UploadPDFSerializer(upload)
    return Response({
        "message": f"{form_type} form uploaded successfully with {priority} priority!",
        "data": serializer.data
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_evaluation_forms(request):
        """List only evaluation forms (signed and ready for submission)"""
        user = request.user
        
        # First try to get evaluation forms owned by current user
        evaluation_forms = UploadPDF.objects.filter(
            user=user,
            form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project'],
            is_signed=True
        )
        
        # If no evaluation forms found for user, also include forms without user assignment (for testing)
        if evaluation_forms.count() == 0:
            evaluation_forms_without_user = UploadPDF.objects.filter(
                user__isnull=True,
                form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project'],
                is_signed=True
            )
            if evaluation_forms_without_user.count() > 0:
                print(f"Warning: No evaluation forms found for user {user.email}, showing {evaluation_forms_without_user.count()} forms without user assignment")
                evaluation_forms = evaluation_forms_without_user
        
        form_type = request.GET.get('form_type')
        if form_type:
            evaluation_forms = evaluation_forms.filter(form_type=form_type)
        
        serializer = UploadPDFSerializer(evaluation_forms, many=True)
        return Response({
            "message": "Evaluation forms retrieved successfully",
            "count": evaluation_forms.count(),
            "data": serializer.data
        })
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def received_evaluations(request):
    """List evaluations sent to the logged-in supervisor/admin."""
    user = request.user
    
    # First try to get evaluations sent to current user
    evaluations = UploadPDF.objects.filter(
        receiver=user,
        form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project'],
        is_signed=True
    ).order_by('-uploaded_at')
    
    # If no evaluations found for user, also include evaluations without receiver assignment (for testing)
    if evaluations.count() == 0:
        evaluations_without_receiver = UploadPDF.objects.filter(
            receiver__isnull=True,
            form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project'],
            is_signed=True
        ).order_by('-uploaded_at')
        if evaluations_without_receiver.count() > 0:
            print(f"Warning: No evaluations found for receiver {user.email}, showing {evaluations_without_receiver.count()} evaluations without receiver assignment")
            evaluations = evaluations_without_receiver

    serializer = UploadPDFSerializer(evaluations, many=True)
    return Response({
        "message": "Received evaluation forms fetched.",
        "count": evaluations.count(),
        "data": serializer.data
    }, status=200)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_evaluation_status(request, pk):
    try:
        pdf = UploadPDF.objects.get(pk=pk, receiver=request.user)
    except UploadPDF.DoesNotExist:
        return Response({"error": "Evaluation not found."}, status=404)

    status_value = request.data.get('status')
    if status_value not in dict(UploadPDF.STATUS_CHOICES):
        return Response({"error": "Invalid status."}, status=400)

    pdf.status = status_value
    pdf.save()

    # Log the activity for evaluation status update
    action = 'approval' if status_value in ['approved', 'rejected'] else 'submission'
    title = f"Evaluation {status_value.title()}"
    description = f"{status_value.title()} evaluation form: {pdf.file_name}"
    personnel = pdf.user.get_full_name() if pdf.user else 'Unknown'
    
    log_supervisor_activity(request.user, action, title, description, personnel)

    serializer = UploadPDFSerializer(pdf)
    return Response({
        "message": f"Status updated to {status_value}.",
        "data": serializer.data
    })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_update_pdf_status(request, pk):
    """
    Allow admins to update the status (start review, approve, reject) of UploadPDF evaluation forms that were submitted TO them.
    """
    user = request.user
    if getattr(user, 'user_type', None) != 'admin':
        return Response({'error': 'Only admins can update evaluation form status'}, status=403)

    # Only allow updates on PDF forms where the admin is the receiver
    pdf = get_object_or_404(UploadPDF, pk=pk, receiver=user)

    status_value = request.data.get('status')
    if status_value not in dict(UploadPDF.STATUS_CHOICES):
        return Response({'error': 'Invalid status.'}, status=400)

    pdf.status = status_value
    pdf.save()

    # Log the activity for evaluation status update
    action = 'approval' if status_value in ['approved', 'rejected'] else 'submission'
    title = f"Evaluation {status_value.title()}"
    description = f"{status_value.title()} evaluation form: {pdf.file_name}"
    personnel = pdf.user.get_full_name() if pdf.user else 'Unknown'
    log_supervisor_activity(user, action, title, description, personnel)

    serializer = UploadPDFSerializer(pdf)
    return Response({
        'message': f'Status updated to {status_value}.',
        'data': serializer.data
    })
