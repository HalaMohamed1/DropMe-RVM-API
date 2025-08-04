from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Material, Machine, Deposit, UserProfile
import uuid

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=15, required=False)
    date_of_birth = serializers.DateField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'phone_number', 'date_of_birth']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        # Remove password_confirm and profile fields
        validated_data.pop('password_confirm')
        phone_number = validated_data.pop('phone_number', '')
        date_of_birth = validated_data.pop('date_of_birth', None)
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update the profile that was created automatically by the signal
        if hasattr(user, 'recycling_profile'):
            profile = user.recycling_profile
            profile.phone_number = phone_number
            profile.date_of_birth = date_of_birth
            profile.save()
        
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password')

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'name', 'points_per_kg', 'description', 'is_active']

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ['id', 'machine_id', 'location', 'latitude', 'longitude', 'is_active']

class DepositCreateSerializer(serializers.ModelSerializer):
    machine_id = serializers.CharField(write_only=True)
    material_name = serializers.CharField(write_only=True)

    class Meta:
        model = Deposit
        fields = ['weight_kg', 'machine_id', 'material_name', 'notes']

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0")
        if value > 100:  # Reasonable upper limit
            raise serializers.ValidationError("Weight cannot exceed 100kg per deposit")
        return value

    def validate_machine_id(self, value):
        try:
            machine = Machine.objects.get(machine_id=value, is_active=True)
            return machine
        except Machine.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive machine ID")

    def validate_material_name(self, value):
        try:
            material = Material.objects.get(name__iexact=value, is_active=True)
            return material
        except Material.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive material type")

    def create(self, validated_data):
        # Replace string values with model instances
        validated_data['machine'] = validated_data.pop('machine_id')
        validated_data['material'] = validated_data.pop('material_name')
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)

class DepositSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    machine_id = serializers.CharField(source='machine.machine_id', read_only=True)
    machine_location = serializers.CharField(source='machine.location', read_only=True)

    class Meta:
        model = Deposit
        fields = [
            'id', 'weight_kg', 'points_earned', 'deposit_time', 
            'transaction_id', 'material_name', 'machine_id', 
            'machine_location', 'notes'
        ]

class UserSummarySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    recent_deposits = serializers.SerializerMethodField()
    deposits_count = serializers.SerializerMethodField()
    favorite_material = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'full_name', 'total_points', 
            'total_weight_recycled', 'deposits_count', 'favorite_material',
            'recent_deposits', 'created_at'
        ]

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def get_recent_deposits(self, obj):
        recent = obj.user.deposits.all()[:5]
        return DepositSerializer(recent, many=True).data

    def get_deposits_count(self, obj):
        return obj.user.deposits.count()

    def get_favorite_material(self, obj):
        from django.db.models import Sum
        favorite = obj.user.deposits.values('material__name').annotate(
            total_weight=Sum('weight_kg')
        ).order_by('-total_weight').first()
        
        return favorite['material__name'] if favorite else None
