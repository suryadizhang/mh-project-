"""
Station RBAC System Integration Test Script
Tests the integration between the API and AI-API with station-aware permissions.
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class StationRBACTester:
    """Integration tester for station-aware RBAC system."""
    
    def __init__(self, api_base_url: str = "http://localhost:8001", ai_api_base_url: str = "http://localhost:8002"):
        self.api_base_url = api_base_url
        self.ai_api_base_url = ai_api_base_url
        self.test_results = []
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
    
    def test_station_authentication(self):
        """Test station-scoped authentication."""
        print("\n=== Testing Station Authentication ===")
        
        try:
            # Test 1: Login with station context
            login_data = {
                "email": "admin@station1.com",
                "password": "test_password",
                "station_id": 1
            }
            
            response = requests.post(f"{self.api_base_url}/auth/station-login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                if "access_token" in token_data and "station_context" in token_data:
                    self.log_test("station_authentication", "PASS", "Station login successful")
                    return token_data["access_token"]
                else:
                    self.log_test("station_authentication", "FAIL", "Missing token or station context")
            else:
                self.log_test("station_authentication", "FAIL", f"Login failed: {response.status_code}")
        
        except Exception as e:
            self.log_test("station_authentication", "ERROR", str(e))
        
        return None
    
    def test_agent_permission_validation(self, token: str):
        """Test agent access based on station permissions."""
        print("\n=== Testing Agent Permission Validation ===")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test different agent access levels
        agents_to_test = [
            ("customer", True, "Should always be accessible"),
            ("support", True, "Should be accessible to customer support+"),
            ("staff", True, "Should be accessible to station admin+"),
            ("admin", False, "Should require admin+ role"),
            ("analytics", False, "Should require admin+ role")
        ]
        
        for agent, should_access, description in agents_to_test:
            try:
                chat_data = {
                    "message": f"Test message for {agent} agent",
                    "context": {"test": True}
                }
                
                headers_with_agent = {**headers, "X-Agent": agent}
                
                response = requests.post(
                    f"{self.ai_api_base_url}/v1/chat",
                    json=chat_data,
                    headers=headers_with_agent
                )
                
                if response.status_code == 200:
                    data = response.json()
                    actual_agent = data.get("agent")
                    
                    if actual_agent == agent:
                        if should_access:
                            self.log_test(f"agent_access_{agent}", "PASS", f"Correctly granted access to {agent}")
                        else:
                            self.log_test(f"agent_access_{agent}", "FAIL", f"Incorrectly granted access to {agent}")
                    else:
                        if not should_access:
                            self.log_test(f"agent_access_{agent}", "PASS", f"Correctly denied access, fallback to {actual_agent}")
                        else:
                            self.log_test(f"agent_access_{agent}", "FAIL", f"Access denied when it should be granted")
                else:
                    self.log_test(f"agent_access_{agent}", "ERROR", f"HTTP {response.status_code}")
            
            except Exception as e:
                self.log_test(f"agent_access_{agent}", "ERROR", str(e))
    
    def test_multi_tenant_isolation(self, token: str):
        """Test multi-tenant data isolation."""
        print("\n=== Testing Multi-Tenant Isolation ===")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # Test 1: Access own station data
            response = requests.get(f"{self.api_base_url}/api/admin/stations/1", headers=headers)
            
            if response.status_code == 200:
                self.log_test("own_station_access", "PASS", "Can access own station data")
            else:
                self.log_test("own_station_access", "FAIL", f"Cannot access own station: {response.status_code}")
            
            # Test 2: Try to access other station data (should fail)
            response = requests.get(f"{self.api_base_url}/api/admin/stations/2", headers=headers)
            
            if response.status_code == 403:
                self.log_test("cross_station_isolation", "PASS", "Correctly blocked cross-station access")
            elif response.status_code == 404:
                self.log_test("cross_station_isolation", "PASS", "Station not found (expected for isolation)")
            else:
                self.log_test("cross_station_isolation", "FAIL", f"Should block cross-station access: {response.status_code}")
        
        except Exception as e:
            self.log_test("multi_tenant_isolation", "ERROR", str(e))
    
    def test_permission_escalation_prevention(self, token: str):
        """Test prevention of permission escalation."""
        print("\n=== Testing Permission Escalation Prevention ===")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # Test 1: Try to create a new station (should fail for non-super-admin)
            station_data = {
                "name": "Unauthorized Station",
                "description": "This should not be created"
            }
            
            response = requests.post(f"{self.api_base_url}/api/admin/stations/", json=station_data, headers=headers)
            
            if response.status_code == 403:
                self.log_test("station_creation_prevention", "PASS", "Correctly blocked station creation")
            else:
                self.log_test("station_creation_prevention", "FAIL", f"Should block station creation: {response.status_code}")
            
            # Test 2: Try to assign super admin role (should fail)
            user_assignment = {
                "user_id": 999,
                "role": "super_admin",
                "permissions": ["*"]
            }
            
            response = requests.post(f"{self.api_base_url}/api/admin/stations/1/users", json=user_assignment, headers=headers)
            
            if response.status_code in [403, 422]:
                self.log_test("role_escalation_prevention", "PASS", "Correctly blocked role escalation")
            else:
                self.log_test("role_escalation_prevention", "FAIL", f"Should block role escalation: {response.status_code}")
        
        except Exception as e:
            self.log_test("permission_escalation_prevention", "ERROR", str(e))
    
    def test_audit_logging(self, token: str):
        """Test audit logging functionality."""
        print("\n=== Testing Audit Logging ===")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # Test 1: Perform an action that should be logged
            chat_data = {
                "message": "Test audit logging",
                "context": {"audit_test": True}
            }
            
            response = requests.post(f"{self.ai_api_base_url}/v1/chat", json=chat_data, headers=headers)
            
            if response.status_code == 200:
                # Wait a moment for logging
                time.sleep(1)
                
                # Test 2: Check audit logs
                response = requests.get(f"{self.api_base_url}/api/admin/stations/1/audit?action=ai_chat", headers=headers)
                
                if response.status_code == 200:
                    logs = response.json()
                    if len(logs) > 0:
                        self.log_test("audit_logging", "PASS", f"Found {len(logs)} audit log entries")
                    else:
                        self.log_test("audit_logging", "WARN", "No audit logs found")
                else:
                    self.log_test("audit_logging", "FAIL", f"Cannot access audit logs: {response.status_code}")
            else:
                self.log_test("audit_logging", "FAIL", f"Initial action failed: {response.status_code}")
        
        except Exception as e:
            self.log_test("audit_logging", "ERROR", str(e))
    
    def test_api_health_checks(self):
        """Test health checks for both APIs."""
        print("\n=== Testing API Health Checks ===")
        
        try:
            # Test API health
            response = requests.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    self.log_test("api_health", "PASS", "API is healthy")
                else:
                    self.log_test("api_health", "WARN", f"API status: {health_data.get('status')}")
            else:
                self.log_test("api_health", "FAIL", f"API health check failed: {response.status_code}")
            
            # Test AI API health
            response = requests.get(f"{self.ai_api_base_url}/v1/health")
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    rbac_enabled = health_data.get("features", {}).get("rbac_enabled", False)
                    station_aware = health_data.get("features", {}).get("station_aware", False)
                    
                    if rbac_enabled and station_aware:
                        self.log_test("ai_api_health", "PASS", "AI API is healthy with RBAC enabled")
                    else:
                        self.log_test("ai_api_health", "WARN", "AI API healthy but RBAC features unclear")
                else:
                    self.log_test("ai_api_health", "WARN", f"AI API status: {health_data.get('status')}")
            else:
                self.log_test("ai_api_health", "FAIL", f"AI API health check failed: {response.status_code}")
        
        except Exception as e:
            self.log_test("health_checks", "ERROR", str(e))
    
    def test_backward_compatibility(self):
        """Test backward compatibility without station context."""
        print("\n=== Testing Backward Compatibility ===")
        
        try:
            # Test AI API without authentication (should default to customer agent)
            chat_data = {
                "message": "Hello, I need help",
                "context": {}
            }
            
            response = requests.post(f"{self.ai_api_base_url}/v1/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("agent") == "customer" and data.get("permission_level") == "public":
                    self.log_test("backward_compatibility", "PASS", "Correctly handles unauthenticated requests")
                else:
                    self.log_test("backward_compatibility", "WARN", f"Unexpected behavior: agent={data.get('agent')}, level={data.get('permission_level')}")
            else:
                self.log_test("backward_compatibility", "FAIL", f"Unauthenticated request failed: {response.status_code}")
        
        except Exception as e:
            self.log_test("backward_compatibility", "ERROR", str(e))
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting Station RBAC Integration Tests")
        print("=" * 50)
        
        # Test API health first
        self.test_api_health_checks()
        
        # Test backward compatibility
        self.test_backward_compatibility()
        
        # Get authentication token
        token = self.test_station_authentication()
        
        if token:
            # Run authenticated tests
            self.test_agent_permission_validation(token)
            self.test_multi_tenant_isolation(token)
            self.test_permission_escalation_prevention(token)
            self.test_audit_logging(token)
        else:
            print("⚠️ Skipping authenticated tests - no valid token")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary report."""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        errors = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"💥 Errors: {errors}")
        
        if failed > 0 or errors > 0:
            print("\n🔍 ISSUES FOUND:")
            for result in self.test_results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  [{result['status']}] {result['test']}: {result['details']}")
        
        success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Station RBAC system is functioning well!")
        elif success_rate >= 60:
            print("⚠️ Station RBAC system has some issues that need attention.")
        else:
            print("🚨 Station RBAC system has significant issues that require immediate attention.")
        
        # Save detailed results
        with open("station_rbac_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: station_rbac_test_results.json")


def main():
    """Main function to run integration tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Station RBAC Integration Tests")
    parser.add_argument("--api-url", default="http://localhost:8001", help="API base URL")
    parser.add_argument("--ai-api-url", default="http://localhost:8002", help="AI API base URL")
    
    args = parser.parse_args()
    
    tester = StationRBACTester(args.api_url, args.ai_api_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()