from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
import logging

from .utils.validators import AdvancedValidators
from .models import Material, Machine, Deposit, UserProfile
from .serializers import DepositCreateSerializer

logger = logging.getLogger('recycling')
security_logger = logging.getLogger('security')

class DepositRateThrottle(UserRateThrottle):
    scope = 'deposits'
    rate = '10/min'  # 10 deposits per minute per user

class AuthRateThrottle(AnonRateThrottle):
    scope = 'auth'
    rate = '5/min'  # 5 auth attempts per minute per IP

@api_view(['POST'])
@throttle_classes([DepositRateThrottle])
@transaction.atomic
def create_deposit_enhanced(request):
    """Enhanced deposit creation with fraud detection and validation"""
    try:
        # Enhanced logging
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        
        logger.info(f"Deposit attempt by {request.user.username} from {client_ip}")
        
        # Pre-validation checks
        try:
            AdvancedValidators.validate_user_behavior(request.user)
        except ValidationError as e:
            security_logger.warning(f"Suspicious behavior detected for user {request.user.username}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Request blocked due to suspicious activity',
                'error_code': 'SUSPICIOUS_BEHAVIOR'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = DepositCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Additional validation
            weight_kg = serializer.validated_data['weight_kg']
            material = serializer.validated_data['material_name']
            machine = serializer.validated_data['machine_id']
            
            try:
                # Validate deposit integrity
                AdvancedValidators.validate_deposit_integrity(
                    request.user, weight_kg, material, machine
                )
                
                # Validate machine capacity
                AdvancedValidators.validate_machine_capacity(
                    machine.machine_id, weight_kg
                )
                
            except ValidationError as e:
                security_logger.warning(f"Deposit validation failed for {request.user.username}: {str(e)}")
                return Response({
                    'success': False,
                    'message': str(e),
                    'error_code': 'VALIDATION_FAILED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create deposit with enhanced tracking
            deposit = serializer.save()
            
            # Cache user's recent activity
            cache_key = f"user_activity_{request.user.id}"
            recent_activity = cache.get(cache_key, [])
            recent_activity.append({
                'action': 'deposit',
                'timestamp': timezone.now().isoformat(),
                'weight': float(weight_kg),
                'material': material.name,
                'ip': client_ip
            })
            cache.set(cache_key, recent_activity[-10:], 3600)  # Keep last 10 activities for 1 hour
            
            # Success response with enhanced data
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
                    'environmental_impact': {
                        'co2_saved_kg': float(deposit.weight_kg) * 2.5,  # Estimated CO2 savings
                        'energy_saved_kwh': float(deposit.weight_kg) * 1.8  # Estimated energy savings
                    }
                },
                'user_totals': {
                    'total_points': float(deposit.user.recycling_profile.total_points),
                    'total_weight_recycled': float(deposit.user.recycling_profile.total_weight_recycled),
                    'rank': get_user_rank(deposit.user)
                }
            }
            
            logger.info(f"Deposit created successfully: {deposit.transaction_id}")
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Invalid deposit data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Unexpected error in deposit creation: {str(e)}")
        return Response({
            'success': False,
            'message': 'An unexpected error occurred. Please try again.',
            'error_code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_user_rank(user):
    """Calculate user's rank based on total points"""
    from django.db.models import Count
    
    user_points = user.recycling_profile.total_points
    higher_users = UserProfile.objects.filter(
        total_points__gt=user_points
    ).count()
    
    return higher_users + 1

@api_view(['GET'])
def system_health_detailed(request):
    """Detailed system health check for monitoring"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from django.core.cache import cache
        import psutil
        
        # Get cached health data
        health_data = cache.get('system_health', {})
        
        # Database health
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_healthy = True
        
        # Cache health
        cache.set('health_test', 'ok', 10)
        cache_healthy = cache.get('health_test') == 'ok'
        
        # Recent activity
        recent_deposits = Deposit.objects.filter(
            deposit_time__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'components': {
                'database': 'healthy' if db_healthy else 'unhealthy',
                'cache': 'healthy' if cache_healthy else 'unhealthy',
                'system_resources': health_data
            },
            'metrics': {
                'recent_deposits_1h': recent_deposits,
                'active_users_24h': UserProfile.objects.filter(
                    user__last_login__gte=timezone.now() - timezone.timedelta(days=1)
                ).count()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
