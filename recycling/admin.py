from django.contrib import admin
from .models import Material, Machine, Deposit, UserProfile

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_per_kg', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['machine_id', 'location', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['machine_id', 'location']
    ordering = ['machine_id']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_points', 'total_weight_recycled', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['total_points', 'total_weight_recycled']
    ordering = ['-total_points']

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['user', 'material', 'weight_kg', 'points_earned', 'machine', 'deposit_time']
    list_filter = ['material', 'machine', 'deposit_time']
    search_fields = ['user__username', 'transaction_id', 'machine__machine_id']
    readonly_fields = ['points_earned', 'transaction_id', 'deposit_time']
    ordering = ['-deposit_time']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['user', 'material', 'machine', 'weight_kg']
        return self.readonly_fields
