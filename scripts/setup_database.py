import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rvm_project.settings')
django.setup()

from django.contrib.auth.models import User
from recycling.models import Machine, Material, Deposit, UserProfile

def setup_initial_data():
    """Setup initial data for the RVM system"""
    print("Setting up initial data for Drop Me RVM system...")
    
    try:
        # Create materials with their point values
        materials_data = [
            {'name': 'Plastic', 'points_per_kg': 1.0, 'description': 'Plastic bottles, containers'},
            {'name': 'Metal', 'points_per_kg': 3.0, 'description': 'Aluminum cans, metal containers'},
            {'name': 'Glass', 'points_per_kg': 2.0, 'description': 'Glass bottles, jars'},
        ]
        
        for material_data in materials_data:
            material, created = Material.objects.get_or_create(
                name=material_data['name'],
                defaults={
                    'points_per_kg': material_data['points_per_kg'],
                    'description': material_data['description']
                }
            )
            if created:
                print(f"[+] Created material: {material.name} ({material.points_per_kg} pts/kg)")
            else:
                print(f"[-] Material already exists: {material.name}")
        
        # Create sample machines
        machines_data = [
            {'machine_id': 'RVM-001', 'location': 'Cairo Mall - New Cairo', 'is_active': True},
            {'machine_id': 'RVM-002', 'location': 'Alexandria Center - Corniche', 'is_active': True},
            {'machine_id': 'RVM-003', 'location': 'Giza Station - Pyramids Area', 'is_active': True},
        ]
        
        for machine_data in machines_data:
            machine, created = Machine.objects.get_or_create(
                machine_id=machine_data['machine_id'],
                defaults={
                    'location': machine_data['location'],
                    'is_active': machine_data['is_active']
                }
            )
            if created:
                print(f"[+] Created machine: {machine.machine_id} at {machine.location}")
            else:
                print(f"[-] Machine already exists: {machine.machine_id}")
        
        # Create a test user
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@dropme.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"[+] Created test user: {test_user.username}")
            
            # Create user profile
            profile, profile_created = UserProfile.objects.get_or_create(user=test_user)
            if profile_created:
                print(f"[+] Created user profile for: {test_user.username}")
        else:
            print(f"[-] Test user already exists: {test_user.username}")
        
        print("\n=== SETUP COMPLETED SUCCESSFULLY! ===")
        print("\nYou can now:")
        print("1. Start the server: python manage.py runserver")
        print("2. Login with: username='testuser', password='testpass123'")
        print("3. Access admin at: http://localhost:8000/admin/")
        print("4. Test API at: http://localhost:8000/api/")
        
    except Exception as e:
        print(f"[ERROR] Error setting up initial data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    setup_initial_data()
