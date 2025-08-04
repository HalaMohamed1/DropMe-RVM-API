#!/usr/bin/env python
"""
Load Testing Script for RVM API
Tests system performance under various load conditions
"""

import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import statistics

class LoadTester:
    def __init__(self, base_url="http://127.0.0.1:8000/api"):
        self.base_url = base_url
        self.token = None
        self.results = []
        self.errors = []
    
    def authenticate(self):
        """Get authentication token"""
        try:
            response = requests.post(f"{self.base_url}/auth/login/", json={
                "username": "testuser",
                "password": "testpass123"
            })
            
            if response.status_code == 200:
                self.token = response.json()['token']
                print(f"Authentication successful")
                return True
            else:
                print(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def make_request(self, endpoint, method="GET", data=None, request_id=None):
        """Make a single request and measure performance"""
        headers = {'Authorization': f'Token {self.token}'} if self.token else {}
        
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                'request_id': request_id,
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'response_time': response_time,
                'success': 200 <= response.status_code < 300,
                'timestamp': datetime.now().isoformat()
            }
            
            if not result['success']:
                result['error'] = response.text[:200]  
            
            return result
            
        except Exception as e:
            end_time = time.time()
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'method': method,
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def load_test_endpoint(self, endpoint, method="GET", data_generator=None, 
                          concurrent_users=10, requests_per_user=10):
        """Load test a specific endpoint"""
        print(f"\n Load testing {method} {endpoint}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Requests per user: {requests_per_user}")
        print(f"   Total requests: {concurrent_users * requests_per_user}")
        
        def user_simulation(user_id):
            """Simulate a single user making multiple requests"""
            user_results = []
            for i in range(requests_per_user):
                data = data_generator(user_id, i) if data_generator else None
                request_id = f"user_{user_id}_req_{i}"
                
                result = self.make_request(endpoint, method, data, request_id)
                user_results.append(result)
                
                time.sleep(0.1)
            
            return user_results
        
        start_time = time.time()
        all_results = []
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_simulation, user_id) 
                      for user_id in range(concurrent_users)]
            
            for future in as_completed(futures):
                user_results = future.result()
                all_results.extend(user_results)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        self.analyze_results(all_results, total_time)
        return all_results
    
    def analyze_results(self, results, total_time):
        """Analyze and print load test results"""
        if not results:
            print(" No results to analyze")
            return
        
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        response_times = [r['response_time'] for r in successful_requests]
        
        print(f"\n Results Summary:")
        print(f"   Total requests: {len(results)}")
        print(f"   Successful: {len(successful_requests)} ({len(successful_requests)/len(results)*100:.1f}%)")
        print(f"   Failed: {len(failed_requests)} ({len(failed_requests)/len(results)*100:.1f}%)")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Requests/second: {len(results)/total_time:.2f}")
        
        if response_times:
            print(f"\n Response Times:")
            print(f"   Average: {statistics.mean(response_times):.3f}s")
            print(f"   Median: {statistics.median(response_times):.3f}s")
            print(f"   Min: {min(response_times):.3f}s")
            print(f"   Max: {max(response_times):.3f}s")
            print(f"   95th percentile: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
        
        # Error analysis
        if failed_requests:
            print(f"\n Error Analysis:")
            error_codes = {}
            for req in failed_requests:
                code = req['status_code']
                error_codes[code] = error_codes.get(code, 0) + 1
            
            for code, count in error_codes.items():
                print(f"   Status {code}: {count} requests")
    
    def deposit_data_generator(self, user_id, request_id):
        """Generate test deposit data"""
        materials = ["Plastic", "Metal", "Glass"]
        machines = ["RVM-001", "RVM-002", "RVM-003"]
        
        return {
            "weight_kg": round(0.5 + (request_id * 0.1), 2),
            "material_name": materials[request_id % len(materials)],
            "machine_id": machines[user_id % len(machines)],
            "notes": f"Load test deposit from user {user_id}, request {request_id}"
        }
    
    def run_comprehensive_load_test(self):
        """Run comprehensive load tests"""
        print(" RVM API LOAD TESTING SUITE")
        print("=" * 50)
        
        if not self.authenticate():
            return
        
        # Test scenarios
        scenarios = [
            {
                'name': 'Light Load - User Summary',
                'endpoint': '/user/summary/',
                'method': 'GET',
                'concurrent_users': 5,
                'requests_per_user': 10
            },
            {
                'name': 'Medium Load - Materials',
                'endpoint': '/materials/',
                'method': 'GET',
                'concurrent_users': 10,
                'requests_per_user': 20
            },
            {
                'name': 'Heavy Load - Deposits',
                'endpoint': '/deposits/',
                'method': 'POST',
                'data_generator': self.deposit_data_generator,
                'concurrent_users': 8,  # Lower due to rate limiting
                'requests_per_user': 5
            },
            {
                'name': 'Stress Test - Mixed Endpoints',
                'endpoint': '/health/',
                'method': 'GET',
                'concurrent_users': 20,
                'requests_per_user': 15
            }
        ]
        
        all_results = []
        
        for scenario in scenarios:
            print(f"\n Running: {scenario['name']}")
            results = self.load_test_endpoint(
                endpoint=scenario['endpoint'],
                method=scenario['method'],
                data_generator=scenario.get('data_generator'),
                concurrent_users=scenario['concurrent_users'],
                requests_per_user=scenario['requests_per_user']
            )
            all_results.extend(results)
            
            print("   Cooling down...")
            time.sleep(2)
        
        self.print_overall_summary(all_results)
        
        with open('load_test_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n Detailed results saved to: load_test_results.json")
    
    def print_overall_summary(self, all_results):
        """Print overall load test summary"""
        print(f"\n OVERALL LOAD TEST SUMMARY")
        print("=" * 50)
        
        if not all_results:
            print("No results to summarize")
            return
        
        total_requests = len(all_results)
        successful = len([r for r in all_results if r['success']])
        failed = total_requests - successful
        
        response_times = [r['response_time'] for r in all_results if r['success']]
        
        print(f"Total Requests: {total_requests}")
        print(f"Success Rate: {successful/total_requests*100:.1f}% ({successful}/{total_requests})")
        print(f"Failure Rate: {failed/total_requests*100:.1f}% ({failed}/{total_requests})")
        
        if response_times:
            print(f"Average Response Time: {statistics.mean(response_times):.3f}s")
            print(f"95th Percentile: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
        
        if successful/total_requests >= 0.95 and statistics.mean(response_times) < 1.0:
            print("VERDICT: API performs well under load!")
        elif successful/total_requests >= 0.90:
            print("VERDICT: API performance is acceptable but could be improved")
        else:
            print("VERDICT: API performance needs improvement")

def main():
    """Main load test runner"""
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    try:
        tester = LoadTester()
        tester.run_comprehensive_load_test()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server!")
        print("Make sure the server is running: python manage.py runserver")
    except KeyboardInterrupt:
        print("\nLoad testing interrupted by user")
    except Exception as e:
        print(f"ERROR: Load testing failed: {e}")

if __name__ == "__main__":
    main()
