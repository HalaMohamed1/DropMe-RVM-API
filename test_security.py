#!/usr/bin/env python
"""
Security Testing Script for RVM API
Tests various security aspects and potential vulnerabilities
"""

import requests
import json
import time
from datetime import datetime

class SecurityTester:
    def __init__(self, base_url="http://127.0.0.1:8000/api"):
        self.base_url = base_url
        self.token = None
        self.results = []
    
    def log_test(self, test_name, passed, message=""):
        """Log security test results"""
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {test_name}: {message}")
        
        self.results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def authenticate(self):
        """Get authentication token"""
        try:
            response = requests.post(f"{self.base_url}/auth/login/", json={
                "username": "testuser",
                "password": "testpass123"
            })
            
            if response.status_code == 200:
                self.token = response.json()['token']
                return True
            return False
        except:
            return False
    
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        print("\n🔍 Testing SQL Injection Protection")
        print("-" * 40)
        
        # Test SQL injection in deposit creation
        sql_payloads = [
            "'; DROP TABLE recycling_deposit; --",
            "' OR '1'='1",
            "'; SELECT * FROM auth_user; --",
            "1' UNION SELECT password FROM auth_user--"
        ]
        
        headers = {'Authorization': f'Token {self.token}'}
        
        for payload in sql_payloads:
            try:
                response = requests.post(f"{self.base_url}/deposits/", 
                    json={
                        "weight_kg": 2.0,
                        "material_name": payload,
                        "machine_id": "RVM-001",
                        "notes": "SQL injection test"
                    },
                    headers=headers
                )
                
                # Should return 400 (validation error) not 500 (server error)
                if response.status_code in [400, 404]:
                    self.log_test("SQL Injection Protection", True, f"Payload blocked: {payload[:20]}...")
                elif response.status_code == 500:
                    self.log_test("SQL Injection Vulnerability", False, f"Server error with payload: {payload[:20]}...")
                else:
                    self.log_test("SQL Injection Test", True, f"Unexpected response: {response.status_code}")
                    
            except Exception as e:
                self.log_test("SQL Injection Test Error", False, f"Exception: {str(e)}")
    
    def test_xss_protection(self):
        """Test for XSS vulnerabilities"""
        print("\n Testing XSS Protection")
        print("-" * 40)
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        headers = {'Authorization': f'Token {self.token}'}
        
        for payload in xss_payloads:
            try:
                response = requests.post(f"{self.base_url}/deposits/", 
                    json={
                        "weight_kg": 2.0,
                        "material_name": "Plastic",
                        "machine_id": "RVM-001",
                        "notes": payload
                    },
                    headers=headers
                )
                
                if response.status_code == 201:
                    response_text = response.text
                    if payload in response_text and '<script>' in response_text:
                        self.log_test("XSS Vulnerability", False, f"Unescaped payload in response")
                    else:
                        self.log_test("XSS Protection", True, f"Payload properly handled")
                else:
                    self.log_test("XSS Protection", True, f"Payload rejected")
                    
            except Exception as e:
                self.log_test("XSS Test Error", False, f"Exception: {str(e)}")
    
    def test_authentication_bypass(self):
        """Test authentication bypass attempts"""
        print("\n Testing Authentication Bypass")
        print("-" * 40)
        
        # Test without token
        response = requests.get(f"{self.base_url}/user/summary/")
        if response.status_code == 401:
            self.log_test("No Token Protection", True, "Request without token rejected")
        else:
            self.log_test("Authentication Bypass", False, f"Request allowed without token: {response.status_code}")
        
        # Test with invalid token
        invalid_headers = {'Authorization': 'Token invalid_token_123'}
        response = requests.get(f"{self.base_url}/user/summary/", headers=invalid_headers)
        if response.status_code == 401:
            self.log_test("Invalid Token Protection", True, "Invalid token rejected")
        else:
            self.log_test("Authentication Bypass", False, f"Invalid token accepted: {response.status_code}")
        
        # Test with malformed token
        malformed_headers = {'Authorization': 'Bearer ' + self.token} 
        response = requests.get(f"{self.base_url}/user/summary/", headers=malformed_headers)
        if response.status_code == 401:
            self.log_test("Malformed Token Protection", True, "Malformed token rejected")
        else:
            self.log_test("Authentication Bypass", False, f"Malformed token accepted: {response.status_code}")
    
    
    def test_data_validation_bypass(self):
        """Test data validation bypass attempts"""
        print("\n Testing Data Validation Bypass")
        print("-" * 40)
        
        headers = {'Authorization': f'Token {self.token}'}
        
        invalid_data_tests = [
            {
                "name": "Negative Weight",
                "data": {"weight_kg": -100, "material_name": "Plastic", "machine_id": "RVM-001"}
            },
            {
                "name": "Excessive Weight",
                "data": {"weight_kg": 99999, "material_name": "Plastic", "machine_id": "RVM-001"}
            },
            {
                "name": "Invalid Material",
                "data": {"weight_kg": 2.0, "material_name": "InvalidMaterial", "machine_id": "RVM-001"}
            },
            {
                "name": "Invalid Machine",
                "data": {"weight_kg": 2.0, "material_name": "Plastic", "machine_id": "INVALID-999"}
            },
            {
                "name": "Missing Required Fields",
                "data": {"weight_kg": 2.0}
            }
        ]
        
        for test in invalid_data_tests:
            try:
                response = requests.post(f"{self.base_url}/deposits/", 
                    json=test["data"], headers=headers)
                
                if response.status_code in [400, 404]:
                    self.log_test(f"Validation: {test['name']}", True, "Invalid data properly rejected")
                elif response.status_code == 201:
                    self.log_test(f"Validation Bypass: {test['name']}", False, "Invalid data accepted")
                else:
                    self.log_test(f"Validation: {test['name']}", True, f"Unexpected response: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Validation Test Error: {test['name']}", False, f"Exception: {str(e)}")
    
    
    def run_security_tests(self):
        """Run all security tests"""
        print(" RVM API SECURITY TESTING SUITE")
        print("=" * 50)
        
        if not self.authenticate():
            print(" Authentication failed. Cannot run security tests.")
            return
        
        print(" Authentication successful. Starting security tests...")
        
        # Run all security tests
        self.test_authentication_bypass()
        self.test_sql_injection()
        self.test_xss_protection()
        self.test_data_validation_bypass()
        
        # Print summary
        self.print_security_summary()
    
    def print_security_summary(self):
        """Print security test summary"""
        print("\n  SECURITY TEST SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.results if r['status'] == 'PASSED'])
        failed = len([r for r in self.results if r['status'] == 'FAILED'])
        total = len(self.results)
        
        print(f"Total Security Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed == 0:
            print(" All security tests passed")
        else:
            print("  Some security tests failed. Review the issues above.")
            print("\nFailed Tests:")
            for result in self.results:
                if result['status'] == 'FAILED':
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save results
        with open('security_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: security_test_results.json")

def main():
    """Main security test runner"""
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    try:
        tester = SecurityTester()
        tester.run_security_tests()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server!")
        print("Make sure the server is running: python manage.py runserver")
    except Exception as e:
        print(f"ERROR: Security testing failed: {e}")

if __name__ == "__main__":
    main()
