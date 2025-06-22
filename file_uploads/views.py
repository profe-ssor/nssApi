from io import BytesIO
import json
import os
from django.conf import settings
from django.shortcuts import render
from django.core.files.base import ContentFile
import fitz
from rest_framework.response import Response 

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from digital360Api.models import MyUser
from file_uploads.models import UploadPDF
from file_uploads.serializers import UploadPDFSerializer

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
@permission_classes([IsAuthenticated])
def list_pdfs(request):
    user = request.user
    """List all PDFs uploaded by the user"""
    pdfs = UploadPDF.objects.filter(user=user)
    serializer = UploadPDFSerializer(pdfs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pdf(request, pk):
    """Get details of a specific PDF"""
    try:
        pdf = UploadPDF.objects.get(pk=pk, user=request.user)
    except UploadPDF.DoesNotExist:
        return Response({"error": "PDF not found"}, status=404)
    
    serializer = UploadPDFSerializer(pdf)
    return Response(serializer.data)

# e: Returns a list of all PDFs that have been signed by the current authenticated user.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_signed_pdfs(request):
    """List all signed PDFs uploaded by the user"""
    signed_pdfs = UploadPDF.objects.filter(is_signed=True, user=request.user)
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
        pdf = UploadPDF.objects.get(pk=pk, user=request.user)
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
    """Upload PDF with evaluation form type, priority, and receiver"""
    pdf_file = request.FILES.get('pdf')
    if not pdf_file:
        return Response({"error": "PDF file is required."}, status=400)
    
    if not pdf_file.name.lower().endswith('.pdf'):
        return Response({"error": "File must be a PDF."}, status=400)

    form_type = request.data.get('form_type', 'General')
    priority = request.data.get('priority', 'medium')
    receiver_id = request.data.get('receiver_id')
    file_path = request.data.get('file_path')

    if form_type not in dict(UploadPDF.FORM_TYPE_CHOICES):
        return Response({"error": "Invalid form type."}, status=400)
    
    if priority not in dict(UploadPDF.PRIORITY_CHOICES):
        return Response({"error": "Invalid priority value."}, status=400)

    receiver = None
    if receiver_id:
        try:
            receiver = MyUser.objects.get(pk=receiver_id)
        except MyUser.DoesNotExist:
            return Response({"error": "Receiver not found."}, status=404)
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
            receiver=receiver
        )
    else:
        # fallback to uploaded file
        pdf_file = request.FILES.get('pdf')
        if not pdf_file:
            return Response({"error": "PDF file or path is required."}, status=400)
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({"error": "File must be a PDF."}, status=400)
        
        upload = UploadPDF.objects.create(
            user=request.user,
            file_name=request.data.get('file_name', os.path.splitext(pdf_file.name)[0]),
            file=pdf_file,
            form_type=form_type,
            priority=priority,
            receiver=receiver
        )
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
        evaluation_forms = UploadPDF.objects.filter(
            user=user,
            form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project'],
            is_signed=True
        )
        
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
    evaluations = UploadPDF.objects.filter(
        receiver=user,
        form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project'],
        is_signed=True
    ).order_by('-uploaded_at')  # ✅ Corrected field

    serializer = UploadPDFSerializer(evaluations, many=True)
    return Response({
        "message": "Received evaluation forms fetched.",
        "count": evaluations.count(),
        "data": serializer.data
    }, status=200)
