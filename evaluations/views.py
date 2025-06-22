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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supervisor_evaluation_list(request):
    """
    List all evaluations assigned to the current supervisor with filtering
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Base queryset - only evaluations supervised by current user
    evaluations = Evaluation.objects.filter(
        supervisor=request.user
    ).select_related('nss_personnel')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        evaluations = evaluations.filter(status=status_filter)
    
    evaluation_type_filter = request.GET.get('evaluation_type')
    if evaluation_type_filter:
        evaluations = evaluations.filter(evaluation_type=evaluation_type_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        evaluations = evaluations.filter(priority=priority_filter)
    
    # Pagination
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))
    
    paginator = Paginator(evaluations, page_size)
    page_obj = paginator.get_page(page)
    
    serializer = EvaluationListSerializer(page_obj.object_list, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def evaluation_detail(request, pk):
    """
    Get detailed view of a specific evaluation
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
    Get dashboard statistics for the supervisor
    """
    # Ensure only supervisors can access this view
    if request.user.user_type != 'supervisor':
        return Response(
            {'error': 'Only supervisors can access dashboard stats'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    supervisor_evaluations = Evaluation.objects.filter(supervisor=request.user)
    today = timezone.now().date()
    
    stats = supervisor_evaluations.aggregate(
        total_pending=Count('id', filter=Q(status='pending')),
        overdue=Count(
            'id', 
            filter=Q(due_date__lt=timezone.now()) & Q(status__in=['pending', 'under_review'])
        ),
        under_review=Count('id', filter=Q(status='under_review')),
        completed_today=Count(
            'id',
            filter=Q(status__in=['approved', 'rejected']) & 
                   Q(reviewed_at__date=today)
        )
    )
    
    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)