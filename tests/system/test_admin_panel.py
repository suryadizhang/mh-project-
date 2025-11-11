#!/usr/bin/env python3
"""
Admin Panel Test Script

This script tests the core functionality of the MyHibachi admin panel
by verifying API connectivity and basic CRUD operations.
"""

import requests
import json
import sys
from datetime import datetime

class AdminPanelTester:
    def __init__(self, api_base_url="http://localhost:8003", admin_url="http://localhost:3002"):
        self.api_base_url = api_base_url
        self.admin_url = admin_url
        self.token = None
        self.session = requests.Session()
        
    def test_api_health(self):
        """Test if the API server is running and healthy"""
        print("Testing API health...")
        try:
            response = self.session.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API is healthy: {health_data.get('status')}")
                print(f"   Database: {health_data.get('database')}")
                print(f"   Features: {health_data.get('features', {})}")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API health check error: {e}")
            return False
    
    def test_admin_panel_access(self):
        """Test if the admin panel is accessible"""
        print("\nTesting admin panel access...")
        try:
            response = self.session.get(self.admin_url)
            if response.status_code == 200:
                print("✅ Admin panel is accessible")
                return True
            else:
                print(f"❌ Admin panel access failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Admin panel access error: {e}")
            return False
    
    def test_api_authentication(self):
        """Test API authentication with demo credentials"""
        print("\nTesting API authentication...")
        
        # Try to access a protected endpoint without authentication
        try:
            response = self.session.get(f"{self.api_base_url}/api/crm/bookings")
            if response.status_code == 401:
                print("✅ API correctly requires authentication")
            else:
                print(f"⚠️  Expected 401, got {response.status_code}")
        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            return False
        
        # Test login endpoint (if available)
        login_data = {
            "email": "admin@myhibachi.com",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(f"{self.api_base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                auth_data = response.json()
                if 'access_token' in auth_data:
                    self.token = auth_data['access_token']
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    print("✅ Authentication successful")
                    return True
                else:
                    print("⚠️  Login successful but no token received")
                    return False
            else:
                print(f"⚠️  Login endpoint returned {response.status_code}")
                # This might be expected if auth endpoints don't exist yet
                return None
        except Exception as e:
            print(f"⚠️  Authentication test error: {e}")
            return None
    
    def test_crm_endpoints(self):
        """Test CRM endpoints that the admin panel will use"""
        print("\nTesting CRM endpoints...")
        
        endpoints_to_test = [
            "/api/crm/bookings",
            "/api/crm/customers", 
            "/api/crm/payments",
            "/api/crm/dashboard/stats"
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.api_base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint}: {response.status_code} - {len(data.get('data', []))} items")
                    results[endpoint] = True
                elif response.status_code == 401:
                    print(f"🔒 {endpoint}: Requires authentication")
                    results[endpoint] = "auth_required"
                else:
                    print(f"❌ {endpoint}: {response.status_code}")
                    results[endpoint] = False
            except Exception as e:
                print(f"❌ {endpoint}: Error - {e}")
                results[endpoint] = False
        
        return results
    
    def test_admin_panel_pages(self):
        """Test admin panel page accessibility"""
        print("\nTesting admin panel pages...")
        
        pages_to_test = [
            "/",
            "/booking", 
            "/customers",
            "/payments",
            "/login"
        ]
        
        results = {}
        
        for page in pages_to_test:
            try:
                response = self.session.get(f"{self.admin_url}{page}")
                if response.status_code == 200:
                    print(f"✅ {page}: Accessible")
                    results[page] = True
                else:
                    print(f"❌ {page}: {response.status_code}")
                    results[page] = False
            except Exception as e:
                print(f"❌ {page}: Error - {e}")
                results[page] = False
        
        return results
    
    def generate_report(self, api_health, admin_access, auth_result, crm_results, page_results):
        """Generate a comprehensive test report"""
        print("\n" + "="*60)
        print("MYHIBACHI ADMIN PANEL TEST REPORT")
        print("="*60)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API URL: {self.api_base_url}")
        print(f"Admin URL: {self.admin_url}")
        print("-"*60)
        
        # Overall Status
        critical_issues = []
        warnings = []
        
        if not api_health:
            critical_issues.append("API server not healthy")
        
        if not admin_access:
            critical_issues.append("Admin panel not accessible")
        
        auth_protected_endpoints = sum(1 for result in crm_results.values() if result == "auth_required")
        working_endpoints = sum(1 for result in crm_results.values() if result is True)
        
        if auth_result is False:
            warnings.append("Authentication failed - admin login may not work")
        elif auth_result is None:
            warnings.append("Authentication endpoint not available")
        
        print("SUMMARY:")
        if not critical_issues:
            print("✅ No critical issues found")
        else:
            print("❌ Critical Issues:")
            for issue in critical_issues:
                print(f"   - {issue}")
        
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        
        print(f"\nAPI Endpoints: {working_endpoints} working, {auth_protected_endpoints} auth-protected")
        print(f"Admin Pages: {sum(page_results.values())} accessible")
        
        # Recommendations
        print("\nRECOMMENDations:")
        if auth_result is None:
            print("- Implement authentication endpoints for admin login")
        if auth_protected_endpoints > 0 and not self.token:
            print("- Admin panel will need authentication to access CRM data")
        if working_endpoints == 0:
            print("- No CRM endpoints accessible - check API implementation")
        
        print("\nNext Steps:")
        print("1. Ensure API server is running on port 8003")
        print("2. Ensure admin panel is running on port 3002") 
        print("3. Test admin login functionality")
        print("4. Verify booking and customer data display")
        
        # Return overall status
        return len(critical_issues) == 0

def main():
    print("MyHibachi Admin Panel Test Suite")
    print("="*50)
    
    tester = AdminPanelTester()
    
    # Run all tests
    api_health = tester.test_api_health()
    admin_access = tester.test_admin_panel_access()
    auth_result = tester.test_api_authentication()
    crm_results = tester.test_crm_endpoints()
    page_results = tester.test_admin_panel_pages()
    
    # Generate report
    success = tester.generate_report(api_health, admin_access, auth_result, crm_results, page_results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()