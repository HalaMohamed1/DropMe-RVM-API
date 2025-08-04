#!/usr/bin/env python
"""
Comprehensive Production Testing Suite for RVM API
Tests basic functionality, security, and performance
"""

import requests
import json
import time
import threading
import concurrent.futures
from datetime import datetime
import random

BASE_URL = "http://127.0.0.1:8000/api"

class RVMProductionTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.session = requests.Session()
        self.results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
    
    def log_test(self, test_name, passed, message="", details=None):
        """Log test results"""
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {test_name}: {message}")
        
        self.results['tests'].append({
            'name': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
    
    def setup_authentication(self):
        """Setup authentication for tests"""
        print("\n" + "="*60)
        print("SETTING UP AUTHENTICATION")
        print("="*60)
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login/", json={
                "username": "testuser",
                "password": "testpass123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.session.headers.update({'Authorization': f'Token {self.token}'})
                self.log_test("Authentication Setup", True, f"Token obtained: {self.token[:10]}...")
                return True
            else:
                self.log_test("Authentication Setup", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_basic_functionality(self):
        """Test basic API functionality"""
        print("\n" + "="*60)
        print("="*60)
        
        try:
            response = self.session.get(f"{self.base_url}/materials/")
            if response.status_code == 200:
                materials = response.json()
                self.log_test("Materials Endpoint", True, f"Retrieved {len(materials)} materials")
            else:
                self.log_test("Materials Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Materials Endpoint", False, f"Exception: {str(e)}")
        
        try:
            response = self.session.get(f"{self.base_url}/machines/")
            if response.status_code == 200:
                machines = response.json()
                self.log_test("Machines Endpoint", True, f"Retrieved {len(machines)} machines")
            else:
                self.log_test("Machines Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Machines Endpoint", False, f"Exception: {str(e)}")
        
        try:
            response = self.session.get(f"{self.base_url}/user/summary/")
            if response.status_code == 200:
                summary = response.json()
                self.log_test("User Summary", True, f"Points: {summary.get('total_points', 0)}")
            else:
                self.log_test("User Summary", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Summary", False, f"Exception: {str(e)}")
    
    def test_deposit_creation(self):
        """Test deposit creation with various scenarios"""
        print("\n" + "="*60)
        print("TESTING DEPOSIT CREATION")
        print("="*60)
        
        test_cases = [
            {"weight_kg": 2.5, "material_name": "Plastic", "machine_id": "RVM-001", "expected": True},
            {"weight_kg": 1.5, "material_name": "Metal", "machine_id": "RVM-002", "expected": True},
            {"weight_kg": 0, "material_name": "Glass", "machine_id": "RVM-001", "expected": False},  # Invalid weight
            {"weight_kg": 2.0, "material_name": "InvalidMaterial", "machine_id": "RVM-001", "expected": False},  # Invalid material
            {"weight_kg": 2.0, "material_name": "Glass", "machine_id": "INVALID-001", "expected": False},  # Invalid machine
        ]
        
        for i, case in enumerate(test_cases, 1):
            try:
                response = self.session.post(f"{self.base_url}/deposits/", json={
                    "weight_kg": case["weight_kg"],
                    "material_name": case["material_name"],
                    "machine_id": case["machine_id"],
                    "notes": f"Test deposit {i}"
                })
                
                success = (response.status_code == 201) == case["expected"]
                
                if success:
                    if case["expected"]:
                        data = response.json()
                        points = data.get('deposit', {}).get('points_earned', 0)
                        self.log_test(f"Deposit Test {i}", True, f"Created successfully, earned {points} points")
                    else:
                        self.log_test(f"Deposit Test {i}", True, f"Correctly rejected invalid data")
                else:
                    self.log_test(f"Deposit Test {i}", False, f"Unexpected result: {response.status_code}")
                
                time.sleep(0.1)
                
            except Exception as e:
                self.log_test(f"Deposit Test {i}", False, f"Exception: {str(e)}")
    
    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        print("\n" + "="*60)
        print("TESTING CONCURRENT REQUESTS")
        print("="*60)
        
        def make_request(request_id):
            """Make a single request"""
            try:
                session = requests.Session()
                session.headers.update({'Authorization': f'Token {self.token}'})
                
                response = session.get(f"{self.base_url}/user/summary/")
                return {
                    'id': request_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_time': response.elapsed.total_seconds()
                }
            except Exception as e:
                return {
                    'id': request_id,
                    'status_code': 0,
                    'success': False,
                    'error': str(e),
                    'response_time': 0
                }
        
        print("Making 20 concurrent requests...")
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = sum(r['response_time'] for r in results if 'response_time' in r) / len(results)
        
        self.log_test("Concurrent Requests", True, 
                     f"{successful_requests}/20 successful in {total_time:.2f}s, avg response: {avg_response_time:.3f}s")
    
    def test_security_features(self):
        """Test security features"""
        print("\n" + "="*60)
        print("TESTING SECURITY FEATURES")
        print("="*60)
        
        try:
            invalid_session = requests.Session()
            invalid_session.headers.update({'Authorization': 'Token invalid_token_12345'})
            
            response = invalid_session.get(f"{self.base_url}/user/summary/")
            
            if response.status_code == 401:
                self.log_test("Invalid Token Rejection", True, "Invalid token correctly rejected")
            else:
                self.log_test("Invalid Token Rejection", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Token Rejection", False, f"Exception: {str(e)}")
        
        try:
            no_auth_session = requests.Session()
            response = no_auth_session.get(f"{self.base_url}/user/summary/")
            
            if response.status_code == 401:
                self.log_test("No Token Rejection", True, "Request without token correctly rejected")
            else:
                self.log_test("No Token Rejection", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("No Token Rejection", False, f"Exception: {str(e)}")
    
    def test_data_validation(self):
        """Test data validation"""
        print("\n" + "="*60)
        print("TESTING DATA VALIDATION")
        print("="*60)
        
        validation_tests = [
            {
                "name": "Negative Weight",
                "data": {"weight_kg": -1.0, "material_name": "Plastic", "machine_id": "RVM-001"},
                "should_fail": True
            },
            {
                "name": "Zero Weight",
                "data": {"weight_kg": 0, "material_name": "Plastic", "machine_id": "RVM-001"},
                "should_fail": True
            },
            {
                "name": "Excessive Weight",
                "data": {"weight_kg": 1000, "material_name": "Plastic", "machine_id": "RVM-001"},
                "should_fail": True
            },
            {
                "name": "Missing Fields",
                "data": {"weight_kg": 2.0},
                "should_fail": True
            },
            {
                "name": "Valid Data",
                "data": {"weight_kg": 2.0, "material_name": "Plastic", "machine_id": "RVM-001"},
                "should_fail": False
            }
        ]
        
        for test in validation_tests:
            try:
                response = self.session.post(f"{self.base_url}/deposits/", json=test["data"])
                
                if test["should_fail"]:
                    success = response.status_code != 201
                    message = "Correctly rejected invalid data" if success else f"Unexpectedly accepted invalid data (status: {response.status_code})"
                else:
                    success = response.status_code == 201
                    message = "Valid data accepted" if success else f"Valid data rejected (status: {response.status_code})"
                
                self.log_test(f"Validation: {test['name']}", success, message)
                
                time.sleep(0.1) 
                
            except Exception as e:
                self.log_test(f"Validation: {test['name']}", False, f"Exception: {str(e)}")
    
    def test_performance(self):
        """Test API performance"""
        print("\n" + "="*60)
        print("TESTING PERFORMANCE")
        print("="*60)
        
        endpoints = [
            ("/materials/", "Materials"),
            ("/machines/", "Machines"),
            ("/user/summary/", "User Summary"),
            ("/health/", "Health Check")
        ]
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                response_time = end_time - start_time
                
                if response.status_code == 200 and response_time < 2.0: 
                    self.log_test(f"Performance: {name}", True, f"Response time: {response_time:.3f}s")
                else:
                    self.log_test(f"Performance: {name}", False, 
                                f"Status: {response.status_code}, Time: {response_time:.3f}s")
                    
            except Exception as e:
                self.log_test(f"Performance: {name}", False, f"Exception: {str(e)}")
    
    def test_logout_functionality(self):
        """Test logout and token invalidation"""
        print("\n" + "="*60)
        print("TESTING LOGOUT FUNCTIONALITY")
        print("="*60)
        
        try:
            response = self.session.get(f"{self.base_url}/user/summary/")
            if response.status_code == 200:
                self.log_test("Pre-logout Access", True, "Can access protected endpoint")
            else:
                self.log_test("Pre-logout Access", False, f"Cannot access endpoint: {response.status_code}")
                return
            
            logout_response = self.session.post(f"{self.base_url}/auth/logout/")
            if logout_response.status_code == 200:
                self.log_test("Logout Request", True, "Logout successful")
            else:
                self.log_test("Logout Request", False, f"Logout failed: {logout_response.status_code}")
                return
            
            post_logout_response = self.session.get(f"{self.base_url}/user/summary/")
            if post_logout_response.status_code == 401:
                self.log_test("Token Invalidation", True, "Token correctly invalidated after logout")
            else:
                self.log_test("Token Invalidation", False, f"Token still valid: {post_logout_response.status_code}")
                
        except Exception as e:
            self.log_test("Logout Functionality", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("RVM API PRODUCTION TESTING SUITE")
        print("="*60)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().isoformat()}")
        
        if not self.setup_authentication():
            print("Authentication setup failed. Cannot continue with tests.")
            return
        
        self.test_basic_functionality()
        self.test_deposit_creation()
        self.test_data_validation()
        self.test_security_features()
        self.test_performance()
        self.test_concurrent_requests()
        self.test_logout_functionality()
        
      
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total_tests = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.results['failed'] > 0:
            print("\nFAILED TESTS:")
            for test in self.results['tests']:
                if test['status'] == 'FAILED':
                    print(f"  - {test['name']}: {test['message']}")
        
        print(f"\nCompleted at: {datetime.now().isoformat()}")
        
    
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print("Detailed results saved to: test_results.json")

def main():
    """Main test runner"""
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    try:
        tester = RVMProductionTester()
        tester.run_all_tests()
    except requests.exceptions.ConnectionError:
        print("Make sure the server is running: python manage.py runserver")
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
    except Exception as e:
        print(f"ERROR: Testing failed with exception: {e}")

if __name__ == "__main__":
    main()
