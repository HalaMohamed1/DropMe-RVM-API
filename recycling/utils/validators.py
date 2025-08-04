from django.core.exceptions import ValidationError
from django.core.cache import cache
import re
import hashlib

class AdvancedValidators:
    """Advanced validation utilities for production"""
    
    @staticmethod
    def validate_deposit_integrity(user, weight_kg, material, machine):
        """Validate deposit for potential fraud"""
        
        # Check for duplicate deposits (same user, weight, material within 1 minute)
        cache_key = f"deposit_hash_{user.id}_{weight_kg}_{material.id}_{machine.id}"
        if cache.get(cache_key):
            raise ValidationError("Duplicate deposit detected")
        cache.set(cache_key, True, 60)  # 1 minute window
        
        # Check for unrealistic weights
        if weight_kg > 50:  # 50kg limit per deposit
            raise ValidationError("Weight exceeds maximum allowed per deposit")
        
        # Check user's daily deposit limit
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        daily_deposits = user.deposits.filter(deposit_time__date=today).count()
        
        if daily_deposits >= 50:  # 50 deposits per day limit
            raise ValidationError("Daily deposit limit exceeded")
        
        return True
    
    @staticmethod
    def validate_machine_capacity(machine_id, weight_kg):
        """Check if machine has capacity for deposit"""
        daily_weight_key = f"machine_daily_weight_{machine_id}"
        daily_weight = cache.get(daily_weight_key, 0)
        
        # Assume 500kg daily capacity per machine
        if daily_weight + weight_kg > 500:
            raise ValidationError("Machine capacity exceeded for today")
        
        cache.set(daily_weight_key, daily_weight + weight_kg, 86400)  # 24 hours
        return True
    
    @staticmethod
    def validate_user_behavior(user):
        """Detect suspicious user behavior patterns"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Check for rapid successive deposits
        recent_deposits = user.deposits.filter(
            deposit_time__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if recent_deposits > 10:
            raise ValidationError("Too many deposits in short time period")
        
        return True
