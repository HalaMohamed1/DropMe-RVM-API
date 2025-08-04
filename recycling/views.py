from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
import logging
import json

from .models import Material, Machine, Deposit, UserProfile
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, MaterialSerializer,
    MachineSerializer, DepositCreateSerializer, DepositSerializer,
    UserSummarySerializer
)

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_welcome(request):
    """Welcome endpoint for the Drop Me RVM API"""
    return Response({
        'message': 'Welcome to Drop Me RVM Backend API! 🌍♻️',
        'version': '1.0.0',
        'description': 'AI-driven Recycling Vending Machine platform for Egypt & MEA',
        'motto': 'Your waste can be your card for your supplies',
        'status': 'operational',
        'server_time': timezone.now().isoformat(),
        'endpoints': {
            'authentication': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/'
            },
            'data': {
                'materials': '/api/materials/',
                'machines': '/api/machines/'
            },
            'deposits': {
                'create': '/api/deposits/',
                'history': '/api/deposits/history/'
            },
            'user': {
                'summary': '/api/user/summary/'
            },
            'admin': {
                'stats': '/api/admin/stats/'
            },
            'system': {
                'health': '/api/health/'
            }
        },
        'test_user': {
            'username': 'testuser',
            'password': 'testpass123'
        },
        'documentation': 'Visit the root URL for complete documentation'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Health check endpoint"""
    try:
        # Check database connectivity
        material_count = Material.objects.count()
        machine_count = Machine.objects.count()
        user_count = User.objects.count()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'counts': {
                'materials': material_count,
                'machines': machine_count,
                'users': user_count
            },
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip()
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'total_points': float(profile.total_points),
                'total_weight_recycled': float(profile.total_weight_recycled)
            },
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Error logging out'}, status=status.HTTP_400_BAD_REQUEST)

class MaterialListView(generics.ListAPIView):
    """List all available materials for recycling"""
    queryset = Material.objects.filter(is_active=True)
    serializer_class = MaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

class MachineListView(generics.ListAPIView):
    """List all active RVM machines"""
    queryset = Machine.objects.filter(is_active=True)
    serializer_class = MachineSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
@transaction.atomic
def create_deposit(request):
    """Create a new recycling deposit"""
    try:
        serializer = DepositCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            deposit = serializer.save()
            
            # Return detailed response
            response_data = {
                'success': True,
                'message': 'Deposit recorded successfully! Thank you for recycling with Drop Me! 🌍♻️',
                'deposit': {
                    'id': deposit.id,
                    'transaction_id': deposit.transaction_id,
                    'weight_kg': float(deposit.weight_kg),
                    'material': deposit.material.name,
                    'points_earned': float(deposit.points_earned),
                    'machine_id': deposit.machine.machine_id,
                    'machine_location': deposit.machine.location,
                    'deposit_time': deposit.deposit_time.isoformat(),
                },
                'user_totals': {
                    'total_points': float(deposit.user.recycling_profile.total_points),
                    'total_weight_recycled': float(deposit.user.recycling_profile.total_weight_recycled)
                }
            }
            
            logger.info(f"Deposit created: {deposit.transaction_id} by {request.user.username}")
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Invalid deposit data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating deposit: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while processing your deposit',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def user_summary(request):
    """Get user's recycling summary and statistics"""
    try:
        profile = request.user.recycling_profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    serializer = UserSummarySerializer(profile)
    
    # Additional statistics
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    
    monthly_stats = request.user.deposits.filter(
        deposit_time__gte=last_30_days
    ).aggregate(
        monthly_points=Sum('points_earned'),
        monthly_weight=Sum('weight_kg'),
        monthly_deposits=Count('id')
    )
    
    # Material breakdown
    material_breakdown = request.user.deposits.values(
        'material__name'
    ).annotate(
        total_weight=Sum('weight_kg'),
        total_points=Sum('points_earned'),
        deposit_count=Count('id')
    ).order_by('-total_weight')
    
    response_data = serializer.data
    response_data.update({
        'monthly_stats': {
            'points_earned': float(monthly_stats['monthly_points'] or 0),
            'weight_recycled': float(monthly_stats['monthly_weight'] or 0),
            'deposits_made': monthly_stats['monthly_deposits'] or 0
        },
        'material_breakdown': [
            {
                'material': item['material__name'],
                'total_weight_kg': float(item['total_weight']),
                'total_points': float(item['total_points']),
                'deposit_count': item['deposit_count']
            }
            for item in material_breakdown
        ]
    })
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def user_deposits(request):
    """Get user's deposit history with pagination"""
    deposits = request.user.deposits.all()
    
    # Optional filtering
    material_filter = request.GET.get('material')
    if material_filter:
        deposits = deposits.filter(material__name__icontains=material_filter)
    
    date_from = request.GET.get('date_from')
    if date_from:
        deposits = deposits.filter(deposit_time__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        deposits = deposits.filter(deposit_time__date__lte=date_to)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(deposits, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    serializer = DepositSerializer(page_obj, many=True)
    
    return Response({
        'deposits': serializer.data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_deposits': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def system_stats(request):
    """Get system-wide recycling statistics (for admin/analytics)"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    from django.db.models import Avg
    
    total_stats = Deposit.objects.aggregate(
        total_weight=Sum('weight_kg'),
        total_points=Sum('points_earned'),
        total_deposits=Count('id'),
        avg_deposit_weight=Avg('weight_kg')
    )
    
    # Top materials
    top_materials = Material.objects.annotate(
        total_deposits=Count('deposits'),
        total_weight=Sum('deposits__weight_kg')
    ).order_by('-total_weight')[:5]
    
    # Active machines stats
    machine_stats = Machine.objects.filter(is_active=True).annotate(
        deposit_count=Count('deposits'),
        total_weight=Sum('deposits__weight_kg')
    ).order_by('-deposit_count')[:10]
    
    return Response({
        'system_totals': {
            'total_weight_recycled': float(total_stats['total_weight'] or 0),
            'total_points_awarded': float(total_stats['total_points'] or 0),
            'total_deposits': total_stats['total_deposits'] or 0,
            'average_deposit_weight': float(total_stats['avg_deposit_weight'] or 0)
        },
        'top_materials': [
            {
                'name': material.name,
                'total_deposits': material.total_deposits,
                'total_weight_kg': float(material.total_weight or 0),
                'points_per_kg': float(material.points_per_kg)
            }
            for material in top_materials
        ],
        'top_machines': [
            {
                'machine_id': machine.machine_id,
                'location': machine.location,
                'deposit_count': machine.deposit_count,
                'total_weight_kg': float(machine.total_weight or 0)
            }
            for machine in machine_stats
        ]
    }, status=status.HTTP_200_OK)
