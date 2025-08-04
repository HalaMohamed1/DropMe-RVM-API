#!/usr/bin/env python
"""
RVM API Test - Professional calculation verification with logout testing
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_rvm_api():
    print("RVM Deposit & Rewards API Test")
    print("=" * 50)
    
    # 1. Login
    print("\n1. Testing authentication...")
    login_response = requests.post(f"{BASE_URL}/auth/login/", json={
        "username": "testuser",
        "password": "testpass123"
    })
    
    if login_response.status_code != 200:
        print("FAILED: Login failed!")
        return
    
    login_data = login_response.json()
    token = login_data['token']
    initial_points = login_data['user']['total_points']
    initial_weight = login_data['user']['total_weight_recycled']
    
    print("PASSED: Login successful")
    print(f"   Username: {login_data['user']['username']}")
    print(f"   Initial Points: {initial_points}")
    print(f"   Initial Weight: {initial_weight} kg")
    
    headers = {"Authorization": f"Token {token}"}
    
    # 2. Get materials
    print("\n2. Getting materials and point values...")
    materials_response = requests.get(f"{BASE_URL}/materials/", headers=headers)
    
    if materials_response.status_code != 200:
        print("FAILED: Materials request failed!")
        return
    
    materials_data = materials_response.json()
    if isinstance(materials_data, dict) and 'results' in materials_data:
        materials = materials_data['results']
    else:
        materials = materials_data
    
    print("PASSED: Materials retrieved")
    material_points = {}
    for material in materials:
        name = material['name']
        points = float(material['points_per_kg'])
        material_points[name] = points
        print(f"   {name}: {points} points/kg")
    
    # 3. Test calculations - 3 test cases only
    print("\n3. Testing reward calculations...")
    print("   Formula: Points = Weight (kg) x Points per kg")
    print()
    
    test_cases = [
        (2.5, "Plastic", "2.5 kg x 1.0 = 2.5 points"),
        (1.5, "Metal", "1.5 kg x 3.0 = 4.5 points"),
        (2.0, "Glass", "2.0 kg x 2.0 = 4.0 points"),
    ]
    
    running_points = float(initial_points)
    running_weight = float(initial_weight)
    
    for i, (weight, material, calculation) in enumerate(test_cases, 1):
        print(f"   Test {i}: Depositing {weight} kg of {material}")
        print(f"   Calculation: {calculation}")
        
        # Create deposit
        deposit_data = {
            "weight_kg": weight,
            "material_name": material,
            "machine_id": "RVM-001",
            "notes": f"Test deposit {i}"
        }
        
        deposit_response = requests.post(f"{BASE_URL}/deposits/", json=deposit_data, headers=headers)
        
        if deposit_response.status_code == 201:
            deposit_result = deposit_response.json()
            earned_points = float(deposit_result['deposit']['points_earned'])
            expected_points = weight * material_points[material]
            
            # Update running totals
            running_points += expected_points
            running_weight += weight
            
            actual_total_points = float(deposit_result['user_totals']['total_points'])
            actual_total_weight = float(deposit_result['user_totals']['total_weight_recycled'])
            
            print(f"   Expected: {expected_points} points | Actual: {earned_points} points")
            print(f"   Running Totals:")
            print(f"      Expected: {running_points} points, {running_weight} kg")
            print(f"      Actual:   {actual_total_points} points, {actual_total_weight} kg")
            
            # Check if calculations match
            if abs(earned_points - expected_points) < 0.01:
                print(f"   PASSED: Individual calculation correct")
            else:
                print(f"   FAILED: Individual calculation incorrect")
            
            if (abs(actual_total_points - running_points) < 0.01 and 
                abs(actual_total_weight - running_weight) < 0.001):
                print(f"   PASSED: Running totals correct")
            else:
                print(f"   FAILED: Running totals incorrect")
                
        else:
            print(f"   FAILED: Deposit failed with status {deposit_response.status_code}")
            print(f"   Error: {deposit_response.text}")
        
        print()
    
    # 4. Final summary
    print("4. Getting user summary...")
    summary_response = requests.get(f"{BASE_URL}/user/summary/", headers=headers)
    
    if summary_response.status_code == 200:
        summary_data = summary_response.json()
        print("PASSED: User summary retrieved")
        print(f"   Username: {summary_data['username']}")
        print(f"   Total Points: {summary_data['total_points']}")
        print(f"   Total Weight Recycled: {summary_data['total_weight_recycled']} kg")
        print(f"   Total Deposits: {summary_data['deposits_count']}")
    
    # 5. Test logout
    print("\n5. Testing logout...")
    try:
        logout_response = requests.post(f"{BASE_URL}/auth/logout/", headers=headers)
        
        if logout_response.status_code == 200:
            print("PASSED: Logout successful")
            
            # Test that token is now invalid
            test_response = requests.get(f"{BASE_URL}/user/summary/", headers=headers)
            if test_response.status_code == 401:
                print("PASSED: Token invalidated after logout")
            else:
                print("FAILED: Token still valid after logout")
                
        else:
            print(f"FAILED: Logout failed with status {logout_response.status_code}")
            print(f"   Error: {logout_response.text}")
            
    except Exception as e:
        print(f"FAILED: Logout error: {e}")
    
    # 6. Calculation Summary
    print("\n" + "=" * 50)
    print("CALCULATION SUMMARY")
    print("=" * 50)
    print("Point Values:")
    for material, points in material_points.items():
        print(f"   {material}: {points} points per kg")
    
    print(f"\nTotal Tests Run: {len(test_cases)}")
    print(f"Expected Final Points: {running_points}")
    print(f"Expected Final Weight: {running_weight} kg")
    
    if summary_response.status_code == 200:
        final_points = float(summary_data['total_points'])
        final_weight = float(summary_data['total_weight_recycled'])
        
        print(f"Actual Final Points: {final_points}")
        print(f"Actual Final Weight: {final_weight} kg")
        
        if (abs(final_points - running_points) < 0.01 and 
            abs(final_weight - running_weight) < 0.001):
            print("\nRESULT: ALL CALCULATIONS CORRECT")
            print("STATUS: RVM API is working correctly")
            print("VERIFICATION: Reward system calculates points accurately")
        else:
            print(f"\nRESULT: CALCULATION MISMATCH DETECTED")
            print(f"Expected: {running_points} points, {running_weight} kg")
            print(f"Actual:   {final_points} points, {final_weight} kg")
    
    print("\nTest completed.")

def main():
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    try:
        test_rvm_api()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server!")
        print("Make sure the server is running: python manage.py runserver")
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")

if __name__ == "__main__":
    main()
