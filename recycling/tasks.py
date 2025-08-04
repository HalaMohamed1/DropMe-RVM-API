from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('recycling')

@shared_task
def process_deposit_analytics():
    """Background task to process deposit analytics"""
    from .models import Deposit, UserProfile
    from django.db.models import Sum, Count
    
    try:
        # Calculate daily statistics
        today = timezone.now().date()
        daily_stats = Deposit.objects.filter(
            deposit_time__date=today
        ).aggregate(
            total_weight=Sum('weight_kg'),
            total_points=Sum('points_earned'),
            total_deposits=Count('id')
        )
        
        # Cache the results
        from django.core.cache import cache
        cache.set('daily_stats', daily_stats, 3600)  # 1 hour cache
        
        logger.info(f"Daily analytics processed: {daily_stats}")
        return daily_stats
        
    except Exception as e:
        logger.error(f"Error processing analytics: {str(e)}")
        raise

@shared_task
def cleanup_expired_tokens():
    """Clean up expired or unused tokens"""
    from rest_framework.authtoken.models import Token
    from django.contrib.auth.models import User
    
    try:
        # Remove tokens for inactive users
        inactive_tokens = Token.objects.filter(
            user__last_login__lt=timezone.now() - timedelta(days=30)
        )
        
        count = inactive_tokens.count()
        inactive_tokens.delete()
        
        logger.info(f"Cleaned up {count} expired tokens")
        return count
        
    except Exception as e:
        logger.error(f"Error cleaning tokens: {str(e)}")
        raise

@shared_task
def send_daily_summary_email():
    """Send daily summary to administrators"""
    try:
        from .models import Deposit
        from django.db.models import Sum, Count
        
        today = timezone.now().date()
        daily_stats = Deposit.objects.filter(
            deposit_time__date=today
        ).aggregate(
            total_weight=Sum('weight_kg'),
            total_points=Sum('points_earned'),
            total_deposits=Count('id'),
            unique_users=Count('user', distinct=True)
        )
        
        message = f"""
        Daily RVM Summary for {today}:
        
        Total Deposits: {daily_stats['total_deposits'] or 0}
        Total Weight: {daily_stats['total_weight'] or 0} kg
        Total Points: {daily_stats['total_points'] or 0}
        Unique Users: {daily_stats['unique_users'] or 0}
        """
        
        send_mail(
            subject=f'RVM Daily Summary - {today}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['admin@dropme.com'],
            fail_silently=False,
        )
        
        logger.info("Daily summary email sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending daily summary: {str(e)}")
        raise

@shared_task
def monitor_system_health():
    """Monitor system health and alert on issues"""
    import psutil
    from django.core.cache import cache
    
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'timestamp': timezone.now().isoformat()
        }
        
        # Cache health data
        cache.set('system_health', health_data, 300)  # 5 minutes
        
        # Alert if thresholds exceeded
        if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
            send_mail(
                subject='RVM System Health Alert',
                message=f'System resources critical: CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['admin@dropme.com'],
                fail_silently=False,
            )
        
        logger.info(f"System health check completed: {health_data}")
        return health_data
        
    except Exception as e:
        logger.error(f"Error monitoring system health: {str(e)}")
        raise
