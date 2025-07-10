from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from .models import Evaluation
from .serializers import (
    EvaluationListSerializer, EvaluationDetailSerializer,
    EvaluationStatusUpdateSerializer, BulkStatusUpdateSerializer,
    DashboardStatsSerializer
)
from file_uploads.models import UploadPDF
from nss_personnel.models import NSSPersonnel
from nss_supervisors.views import log_evaluation_approval, log_evaluation_review_start
from file_uploads.serializers import UploadPDFListSerializer
from nss_supervisors.models import ActivityLog
from nss_supervisors.serializers import ActivityLogSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supervisor_evaluation_list(request):
    """
    List all evaluations and PDF forms assigned to the current supervisor with filtering
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # --- Evaluation model ---
    # Only show evaluations where the supervisor is the supervisor
    eval_qs = Evaluation.objects.filter(supervisor=request.user).select_related('nss_personnel')
    
    # Apply filters to evaluations
    status_filter = request.GET.get('status')
    if status_filter:
        eval_qs = eval_qs.filter(status=status_filter)
    
    evaluation_type_filter = request.GET.get('evaluation_type')
    if evaluation_type_filter:
        eval_qs = eval_qs.filter(evaluation_type=evaluation_type_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        eval_qs = eval_qs.filter(priority=priority_filter)

    # --- UploadPDF model ---
    # Only show PDF forms where the supervisor is the receiver
    pdf_qs = UploadPDF.objects.filter(
        receiver=request.user, 
        is_signed=True, 
        form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']
    )
    
    # Apply filters to PDF forms
    if status_filter:
        pdf_qs = pdf_qs.filter(status=status_filter)
    if evaluation_type_filter:
        pdf_qs = pdf_qs.filter(form_type=evaluation_type_filter.capitalize())
    if priority_filter:
        pdf_qs = pdf_qs.filter(priority=priority_filter)

    # Pagination
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))

    # Combine and sort by due_date/created_at descending
    eval_list = list(eval_qs)
    pdf_list = list(pdf_qs)
    
    # Tag source for frontend
    eval_serialized = EvaluationListSerializer(eval_list, many=True).data
    for e in eval_serialized:
        e['source'] = 'evaluation'
    
    pdf_serialized = UploadPDFListSerializer(pdf_list, many=True).data
    for p in pdf_serialized:
        p['source'] = 'pdf'
    
    # Merge and sort
    combined = eval_serialized + pdf_serialized
    combined.sort(key=lambda x: x.get('due_date') or x.get('uploaded_at') or '', reverse=True)

    # Paginate
    total = len(combined)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = combined[start:end]
    total_pages = (total + page_size - 1) // page_size

    return Response({
        'results': paginated,
        'count': total,
        'total_pages': total_pages,
        'current_page': page,
        'next': page < total_pages,
        'previous': page > 1
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def evaluation_detail(request, pk):
    """
    Get detailed information about a specific evaluation
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    evaluation = get_object_or_404(
        Evaluation, 
        pk=pk, 
        supervisor=request.user
    )
    
    serializer = EvaluationDetailSerializer(evaluation)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def evaluation_status_update(request, pk):
    """
    Update evaluation status (Start Review, Approve, Reject)
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can update evaluation status'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    evaluation = get_object_or_404(
        Evaluation, 
        pk=pk, 
        supervisor=request.user
    )
    
    serializer = EvaluationStatusUpdateSerializer(
        evaluation, 
        data=request.data, 
        partial=True
    )
    
    if serializer.is_valid():
        # Set reviewed_at timestamp for approved/rejected statuses
        if serializer.validated_data.get('status') in ['approved', 'rejected']:
            serializer.save(reviewed_at=timezone.now())
        else:
            serializer.save()
        
        # Log the activity based on the action
        if serializer.validated_data.get('status') == 'under_review':
            log_evaluation_review_start(request.user, evaluation)
        else:
            log_evaluation_approval(request.user, evaluation)
        
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_status_update(request):
    """
    Bulk approve or reject multiple evaluations
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can perform bulk updates'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = BulkStatusUpdateSerializer(data=request.data)
    if serializer.is_valid():
        evaluation_ids = serializer.validated_data['evaluation_ids']
        new_status = serializer.validated_data['status']
        comments = serializer.validated_data.get('supervisor_comments', '')
        
        # Only update evaluations supervised by current user
        evaluations = Evaluation.objects.filter(
            id__in=evaluation_ids,
            supervisor=request.user
        )
        
        if not evaluations.exists():
            return Response(
                {'error': 'No valid evaluations found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update all selected evaluations
        update_data = {
            'status': new_status,
            'reviewed_at': timezone.now(),
        }
        if comments:
            update_data['supervisor_comments'] = comments
            
        updated_count = evaluations.update(**update_data)
        
        # Log activities for each updated evaluation
        for evaluation in evaluations:
            log_evaluation_approval(request.user, evaluation)
        
        return Response({
            'message': f'{updated_count} evaluations updated successfully',
            'updated_count': updated_count,
            'status': new_status
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics for the current supervisor
    Includes both Evaluation model and signed UploadPDF data
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get evaluations for current supervisor (Evaluation model)
    evaluations = Evaluation.objects.filter(supervisor=request.user)
    
    # Get signed PDF evaluation forms for current supervisor (UploadPDF model)
    signed_pdf_forms = UploadPDF.objects.filter(
        receiver=request.user,
        form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project'],
        is_signed=True
    )
    
    # Calculate stats from Evaluation model
    eval_total_submissions = evaluations.count()
    eval_total_pending = evaluations.filter(status='pending').count()
    eval_approved = evaluations.filter(status='approved').count()
    eval_rejected = evaluations.filter(status='rejected').count()
    eval_under_review = evaluations.filter(status='under_review').count()
    
    # Calculate overdue evaluations
    eval_overdue = evaluations.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'under_review']
    ).count()
    
    # Calculate completed today from evaluations
    today = timezone.now().date()
    eval_completed_today = evaluations.filter(
        status__in=['approved', 'rejected'],
        reviewed_at__date=today
    ).count()
    
    # Calculate stats from UploadPDF model
    pdf_total_submissions = signed_pdf_forms.count()
    pdf_total_pending = signed_pdf_forms.filter(status='pending').count()
    pdf_approved = signed_pdf_forms.filter(status='approved').count()
    pdf_rejected = signed_pdf_forms.filter(status='rejected').count()
    pdf_under_review = signed_pdf_forms.filter(status='under_review').count()
    
    # Calculate overdue PDF forms
    pdf_overdue = signed_pdf_forms.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'under_review']
    ).count()
    
    # Calculate completed today from PDF forms
    pdf_completed_today = signed_pdf_forms.filter(
        status__in=['approved', 'rejected'],
        submitted_date__date=today
    ).count()
    
    # Combine stats from both models
    stats = {
        'total_submissions': eval_total_submissions + pdf_total_submissions,
        'total_pending': eval_total_pending + pdf_total_pending,
        'approved': eval_approved + pdf_approved,
        'rejected': eval_rejected + pdf_rejected,
        'overdue': eval_overdue + pdf_overdue,
        'under_review': eval_under_review + pdf_under_review,
        'completed_today': eval_completed_today + pdf_completed_today
    }
    
    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personnel_submissions(request):
    """
    Get personnel submissions data for the current supervisor
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get evaluations supervised by current user
    supervisor_evaluations = Evaluation.objects.filter(
        supervisor=request.user
    ).select_related('nss_personnel')
    
    # Get UploadPDF forms supervised by current user
    supervisor_evaluation_forms = UploadPDF.objects.filter(
        receiver=request.user,
        form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']
    ).select_related('user')
    
    # Aggregate data by personnel
    personnel_stats = {}
    
    # Process Evaluation model data
    for evaluation in supervisor_evaluations:
        personnel_name = evaluation.nss_personnel.get_full_name() if evaluation.nss_personnel else 'Unknown'
        if not personnel_name.strip() and evaluation.nss_personnel:
            personnel_name = evaluation.nss_personnel.email
        personnel_id = str(evaluation.nss_personnel.id) if evaluation.nss_personnel else 'unknown'
        
        if personnel_id not in personnel_stats:
            personnel_stats[personnel_id] = {
                'personnelId': personnel_id,
                'name': personnel_name,
                'region': 'N/A',  # Could be added to model later
                'submissions': 0,
                'approved': 0,
                'pending': 0,
                'rejected': 0,
                'lastActivity': evaluation.created_at
            }
        
        personnel_stats[personnel_id]['submissions'] += 1
        
        if evaluation.status == 'approved':
            personnel_stats[personnel_id]['approved'] += 1
        elif evaluation.status == 'pending':
            personnel_stats[personnel_id]['pending'] += 1
        elif evaluation.status == 'rejected':
            personnel_stats[personnel_id]['rejected'] += 1
        
        # Update last activity
        if evaluation.updated_at > personnel_stats[personnel_id]['lastActivity']:
            personnel_stats[personnel_id]['lastActivity'] = evaluation.updated_at
    
    # Process UploadPDF model data
    for form in supervisor_evaluation_forms:
        personnel_name = form.user.get_full_name() if form.user else 'Unknown'
        if not personnel_name.strip() and form.user:
            personnel_name = form.user.email
        personnel_id = str(form.user.id) if form.user else 'unknown'
        
        if personnel_id not in personnel_stats:
            personnel_stats[personnel_id] = {
                'personnelId': personnel_id,
                'name': personnel_name,
                'region': 'N/A',
                'submissions': 0,
                'approved': 0,
                'pending': 0,
                'rejected': 0,
                'lastActivity': form.uploaded_at
            }
        
        personnel_stats[personnel_id]['submissions'] += 1
        
        if form.status == 'approved':
            personnel_stats[personnel_id]['approved'] += 1
        elif form.status == 'pending':
            personnel_stats[personnel_id]['pending'] += 1
        elif form.status == 'rejected':
            personnel_stats[personnel_id]['rejected'] += 1
        
        # Update last activity
        if form.uploaded_at > personnel_stats[personnel_id]['lastActivity']:
            personnel_stats[personnel_id]['lastActivity'] = form.uploaded_at
    
    # Convert to list and sort by last activity
    personnel_list = list(personnel_stats.values())
    personnel_list.sort(key=lambda x: x['lastActivity'], reverse=True)
    
    return Response(personnel_list)

# --- ADMIN DASHBOARD STATS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_stats(request):
    user = request.user
    if getattr(user, 'user_type', None) != 'admin':
        return Response({'error': 'Only admins can access this endpoint'}, status=403)
    
    # --- Evaluation model ---
    # Only count evaluations where the admin is the supervisor
    evaluations = Evaluation.objects.filter(supervisor=user)
    
    # --- UploadPDF model ---
    # Only count PDF forms where the admin is the receiver
    pdf_forms = UploadPDF.objects.filter(
        receiver=user, 
        is_signed=True,
        form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']
    )

    now = timezone.now()
    today = now.date()

    eval_total_submissions = evaluations.count()
    eval_total_pending = evaluations.filter(status='pending').count()
    eval_approved = evaluations.filter(status='approved').count()
    eval_rejected = evaluations.filter(status='rejected').count()
    eval_under_review = evaluations.filter(status='under_review').count()
    eval_overdue = evaluations.filter(
        due_date__lt=now,
        status__in=['pending', 'under_review']
    ).count()
    eval_completed_today = evaluations.filter(
        status__in=['approved', 'rejected'],
        reviewed_at__date=today
    ).count()

    pdf_total_submissions = pdf_forms.count()
    pdf_total_pending = pdf_forms.filter(status='pending').count()
    pdf_approved = pdf_forms.filter(status='approved').count()
    pdf_rejected = pdf_forms.filter(status='rejected').count()
    pdf_under_review = pdf_forms.filter(status='under_review').count()
    pdf_overdue = pdf_forms.filter(
        due_date__lt=now,
        status__in=['pending', 'under_review']
    ).count()
    pdf_completed_today = pdf_forms.filter(
        status__in=['approved', 'rejected'],
        submitted_date__date=today
    ).count()

    stats = {
        'totalSubmissions': eval_total_submissions + pdf_total_submissions,
        'pendingReviews': eval_total_pending + pdf_total_pending,
        'approvedSubmissions': eval_approved + pdf_approved,
        'rejectedSubmissions': eval_rejected + pdf_rejected,
        'totalPersonnel': 0,  # Not relevant in this restrictive view
        'activeSupervisors': 0,  # Not relevant in this restrictive view
        'completedToday': eval_completed_today + pdf_completed_today
    }
    return Response(stats)

# --- ADMIN EVALUATIONS LIST ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_evaluations_list(request):
    """
    List all Evaluation and UploadPDF forms that were directly submitted TO the admin, with filters and pagination.
    """
    user = request.user
    if getattr(user, 'user_type', None) != 'admin':
        return Response({'error': 'Only admins can access this endpoint'}, status=403)
    
    # --- Evaluation model ---
    # Only show evaluations where the admin is the supervisor
    eval_qs = Evaluation.objects.filter(supervisor=user)
    
    # Filters
    status_filter = request.GET.get('status')
    if status_filter:
        eval_qs = eval_qs.filter(status=status_filter)
    type_filter = request.GET.get('evaluation_type')
    if type_filter:
        eval_qs = eval_qs.filter(evaluation_type=type_filter)
    priority_filter = request.GET.get('priority')
    if priority_filter:
        eval_qs = eval_qs.filter(priority=priority_filter)

    # --- UploadPDF model ---
    # Only show PDF forms where the admin is the receiver
    pdf_qs = UploadPDF.objects.filter(
        receiver=user, 
        is_signed=True, 
        form_type__in=['Monthly', 'Quarterly', 'Annual', 'Project']
    )
    
    if status_filter:
        pdf_qs = pdf_qs.filter(status=status_filter)
    if type_filter:
        pdf_qs = pdf_qs.filter(form_type=type_filter.capitalize())
    if priority_filter:
        pdf_qs = pdf_qs.filter(priority=priority_filter)

    # Pagination
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))

    # Combine and sort by due_date/created_at descending
    eval_list = list(eval_qs)
    pdf_list = list(pdf_qs)
    
    # Tag source for frontend
    eval_serialized = EvaluationListSerializer(eval_list, many=True).data
    for e in eval_serialized:
        e['source'] = 'evaluation'
    
    pdf_serialized = UploadPDFListSerializer(pdf_list, many=True).data
    for p in pdf_serialized:
        p['source'] = 'pdf'
    
    # Merge and sort
    combined = eval_serialized + pdf_serialized
    combined.sort(key=lambda x: x.get('due_date') or x.get('uploaded_at') or '', reverse=True)

    # Paginate
    total = len(combined)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = combined[start:end]
    total_pages = (total + page_size - 1) // page_size

    return Response({
        'results': paginated,
        'count': total,
        'total_pages': total_pages,
        'current_page': page,
        'next': page < total_pages,
        'previous': page > 1
    })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_evaluation_status_update(request, pk):
    """
    Allow admins to update the status (start review, approve, reject) of Evaluation objects that were submitted TO them.
    """
    user = request.user
    if getattr(user, 'user_type', None) != 'admin':
        return Response({'error': 'Only admins can update evaluation status'}, status=403)
    
    # Only allow updates on evaluations where the admin is the supervisor
    evaluation = get_object_or_404(Evaluation, pk=pk, supervisor=user)

    serializer = EvaluationStatusUpdateSerializer(
        evaluation,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        # Set reviewed_at timestamp for approved/rejected statuses
        if serializer.validated_data.get('status') in ['approved', 'rejected']:
            serializer.save(reviewed_at=timezone.now())
        else:
            serializer.save()
        # Log the activity
        if serializer.validated_data.get('status') == 'under_review':
            log_evaluation_review_start(user, evaluation)
        else:
            log_evaluation_approval(user, evaluation)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_activity_logs(request):
    user = request.user
    if getattr(user, 'user_type', None) != 'admin':
        return Response({'error': 'Only admins can access this endpoint'}, status=403)
    # Get all supervisors assigned to this admin
    admin_profile = user.administrator_profile
    supervisor_ids = admin_profile.assigned_supervisors.values_list('id', flat=True)
    # Get recent activity logs for these supervisors
    limit = int(request.GET.get('limit', 15))
    activities = ActivityLog.objects.filter(supervisor__id__in=supervisor_ids).order_by('-timestamp')[:limit]
    serializer = ActivityLogSerializer(activities, many=True)
    return Response(serializer.data)