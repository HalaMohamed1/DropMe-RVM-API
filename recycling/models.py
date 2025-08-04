from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import uuid

class Material(models.Model):
    """Material types that can be recycled"""
    name = models.CharField(max_length=50, unique=True)
    points_per_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.points_per_kg} pts/kg)"

class Machine(models.Model):
    """RVM machines deployed across locations"""
    machine_id = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['machine_id']

    def __str__(self):
        return f"{self.machine_id} - {self.location}"

class UserProfile(models.Model):
    """Extended user profile for recycling data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recycling_profile')
    total_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_weight_recycled = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.total_points} pts"

class Deposit(models.Model):
    """Individual recycling deposits made by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='deposits')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='deposits')
    weight_kg = models.DecimalField(
        max_digits=8, 
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    points_earned = models.DecimalField(max_digits=8, decimal_places=2)
    deposit_time = models.DateTimeField(auto_now_add=True)
    
    # Additional tracking fields
    transaction_id = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-deposit_time']
        indexes = [
            models.Index(fields=['user', '-deposit_time']),
            models.Index(fields=['machine', '-deposit_time']),
            models.Index(fields=['material']),
        ]

    def save(self, *args, **kwargs):
        # Auto-calculate points if not set
        if not self.points_earned:
            self.points_earned = self.weight_kg * self.material.points_per_kg
        
        # Generate transaction ID if not set
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.weight_kg}kg {self.material.name} - {self.points_earned} pts"

# Signal handlers for automatic profile creation and updates
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'recycling_profile'):
        instance.recycling_profile.save()

@receiver(post_save, sender=Deposit)
def update_user_totals(sender, instance, created, **kwargs):
    """Update user totals when deposit is created"""
    if created:
        profile, profile_created = UserProfile.objects.get_or_create(user=instance.user)
        
        # Recalculate totals from all deposits
        from django.db.models import Sum
        totals = Deposit.objects.filter(user=instance.user).aggregate(
            total_points=Sum('points_earned'),
            total_weight=Sum('weight_kg')
        )
        
        profile.total_points = totals['total_points'] or 0
        profile.total_weight_recycled = totals['total_weight'] or 0
        profile.save()
