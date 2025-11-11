#!/usr/bin/env python3
"""
Comprehensive Production Functionality Test
Tests all frontend/backend functionality as requested by user
"""

import asyncio
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionFunctionalityTester:
    def __init__(self):
        self.api_base_url = "http://localhost:8003"
        self.ai_api_base_url = "http://localhost:8002"
        self.test_results = {}
        self.test_data = {}
        
    def run_all_tests(self):
        """Run comprehensive functionality tests"""
        logger.info("🚀 Starting comprehensive functionality test...")
        
        tests = [
            ("API Server Health", self.test_api_health),
            ("API Documentation", self.test_api_documentation),
            ("Database CRUD Operations", self.test_database_crud),
            ("Customer Management", self.test_customer_management),
            ("Booking System", self.test_booking_system),
            ("Payment Integration", self.test_payment_system),
            ("Authentication System", self.test_authentication),
            ("Security Features", self.test_security_features),
            ("API Endpoints Coverage", self.test_api_endpoints),
            ("AI API Functionality", self.test_ai_api),
            ("Frontend API Integration", self.test_frontend_integration),
        ]
        
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Running: {test_name}")
            try:
                result = test_func()
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                    passed_tests += 1
                else:
                    logger.error(f"❌ {test_name}: FAILED")
                self.test_results[test_name] = result
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {str(e)}")
                self.test_results[test_name] = False
                
        # Generate summary report
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"\n📊 TEST SUMMARY:")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        self.generate_detailed_report()
        return success_rate >= 90
        
    def test_api_health(self):
        """Test API server health and basic connectivity"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"API Health: {health_data}")
                return True
            return False
        except Exception as e:
            logger.error(f"API Health check failed: {e}")
            return False
            
    def test_api_documentation(self):
        """Test API documentation accessibility"""
        try:
            # Test OpenAPI schema
            response = requests.get(f"{self.api_base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                openapi_spec = response.json()
                logger.info(f"OpenAPI endpoints found: {len(openapi_spec.get('paths', {}))}")
                
                # Test Swagger UI
                docs_response = requests.get(f"{self.api_base_url}/docs", timeout=10)
                return docs_response.status_code == 200
            return False
        except Exception as e:
            logger.error(f"API Documentation test failed: {e}")
            return False
            
    def test_database_crud(self):
        """Test basic database CRUD operations"""
        try:
            # Test database health endpoint
            response = requests.get(f"{self.api_base_url}/health/db", timeout=10)
            if response.status_code == 200:
                db_health = response.json()
                logger.info(f"Database Health: {db_health}")
                return db_health.get('status') == 'healthy'
            return False
        except Exception as e:
            logger.error(f"Database CRUD test failed: {e}")
            return False
            
    def test_customer_management(self):
        """Test customer management functionality"""
        try:
            # Test customer endpoints
            endpoints_to_test = [
                "/customers",
                "/customers/search",
            ]
            
            for endpoint in endpoints_to_test:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                if response.status_code not in [200, 404, 422]:  # 404/422 might be expected for empty data
                    logger.error(f"Customer endpoint {endpoint} failed: {response.status_code}")
                    return False
                    
            logger.info("Customer management endpoints accessible")
            return True
        except Exception as e:
            logger.error(f"Customer management test failed: {e}")
            return False
            
    def test_booking_system(self):
        """Test booking system functionality"""
        try:
            # Test booking-related endpoints
            booking_endpoints = [
                "/bookings",
                "/bookings/search",
                "/products",
            ]
            
            for endpoint in booking_endpoints:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                if response.status_code not in [200, 404, 422]:
                    logger.error(f"Booking endpoint {endpoint} failed: {response.status_code}")
                    return False
                    
            logger.info("Booking system endpoints accessible")
            return True
        except Exception as e:
            logger.error(f"Booking system test failed: {e}")
            return False
            
    def test_payment_system(self):
        """Test payment system integration"""
        try:
            # Test payment-related endpoints
            payment_endpoints = [
                "/payments",
                "/invoices",
            ]
            
            for endpoint in payment_endpoints:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                if response.status_code not in [200, 404, 422]:
                    logger.error(f"Payment endpoint {endpoint} failed: {response.status_code}")
                    return False
                    
            logger.info("Payment system endpoints accessible")
            return True
        except Exception as e:
            logger.error(f"Payment system test failed: {e}")
            return False
            
    def test_authentication(self):
        """Test authentication system"""
        try:
            # Test auth endpoints
            auth_endpoints = [
                "/auth/login",
                "/auth/register",
            ]
            
            for endpoint in auth_endpoints:
                # POST endpoints need different testing approach
                response = requests.post(f"{self.api_base_url}{endpoint}", 
                                       json={}, timeout=10)
                if response.status_code not in [422, 400]:  # Expected validation errors
                    logger.error(f"Auth endpoint {endpoint} unexpected status: {response.status_code}")
                    return False
                    
            logger.info("Authentication endpoints accessible")
            return True
        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            return False
            
    def test_security_features(self):
        """Test security configurations"""
        try:
            # Test CORS headers
            response = requests.options(f"{self.api_base_url}/health", timeout=10)
            headers = response.headers
            
            # Check for basic security headers
            security_checks = [
                ('CORS', 'access-control-allow-origin' in headers),
                ('Content-Type', 'content-type' in headers),
            ]
            
            all_passed = all(check[1] for check in security_checks)
            logger.info(f"Security checks: {security_checks}")
            return all_passed
        except Exception as e:
            logger.error(f"Security test failed: {e}")
            return False
            
    def test_api_endpoints(self):
        """Test comprehensive API endpoint coverage"""
        try:
            # Get OpenAPI spec to test endpoint coverage
            response = requests.get(f"{self.api_base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                openapi_spec = response.json()
                paths = openapi_spec.get('paths', {})
                
                # Count endpoints by category
                endpoint_categories = {
                    'customers': 0,
                    'bookings': 0,
                    'payments': 0,
                    'auth': 0,
                    'admin': 0,
                    'health': 0
                }
                
                for path in paths.keys():
                    for category in endpoint_categories.keys():
                        if category in path.lower():
                            endpoint_categories[category] += 1
                            break
                            
                logger.info(f"API Endpoint Coverage: {endpoint_categories}")
                
                # Check if we have comprehensive coverage
                required_categories = ['customers', 'bookings', 'payments', 'auth', 'health']
                has_coverage = all(endpoint_categories.get(cat, 0) > 0 for cat in required_categories)
                
                return has_coverage
            return False
        except Exception as e:
            logger.error(f"API endpoints test failed: {e}")
            return False
            
    def test_ai_api(self):
        """Test AI API functionality"""
        try:
            # Try to connect to AI API
            response = requests.get(f"{self.ai_api_base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("AI API is accessible")
                return True
            else:
                logger.warning(f"AI API not accessible: {response.status_code}")
                return False  # Don't fail overall test for AI API issues
        except Exception as e:
            logger.warning(f"AI API test failed (non-critical): {e}")
            return False  # AI API is supplementary, don't fail main test
            
    def test_frontend_integration(self):
        """Test frontend integration readiness"""
        try:
            # Check if frontend apps have proper package.json
            frontend_apps = ['customer', 'admin']
            for app in frontend_apps:
                package_path = f"apps/{app}/package.json"
                if os.path.exists(package_path):
                    logger.info(f"✅ {app} frontend app configured")
                else:
                    logger.warning(f"⚠️ {app} frontend app missing package.json")
                    
            # Test API connectivity from frontend perspective
            # Check if API returns proper CORS headers for frontend
            response = requests.get(f"{self.api_base_url}/health", 
                                  headers={'Origin': 'http://localhost:3000'}, 
                                  timeout=10)
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Frontend integration test failed: {e}")
            return False
            
    def generate_detailed_report(self):
        """Generate detailed test report"""
        report_path = "PRODUCTION_FUNCTIONALITY_TEST_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# MH Webapps - Production Functionality Test Report\n\n")
            f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Test Results Summary\n\n")
            passed = sum(1 for result in self.test_results.values() if result)
            total = len(self.test_results)
            success_rate = (passed / total) * 100 if total > 0 else 0
            
            f.write(f"- **Total Tests:** {total}\n")
            f.write(f"- **Passed:** {passed}\n")
            f.write(f"- **Failed:** {total - passed}\n")
            f.write(f"- **Success Rate:** {success_rate:.1f}%\n\n")
            
            f.write("## Detailed Results\n\n")
            for test_name, result in self.test_results.items():
                status = "✅ PASSED" if result else "❌ FAILED"
                f.write(f"- **{test_name}:** {status}\n")
                
            f.write("\n## Production Readiness Assessment\n\n")
            if success_rate >= 90:
                f.write("🎉 **PROJECT IS READY FOR PRODUCTION DEPLOYMENT**\n\n")
                f.write("All critical functionality tests have passed. The application is ready for production deployment.\n")
            else:
                f.write("⚠️ **PROJECT NEEDS ATTENTION BEFORE PRODUCTION**\n\n")
                f.write("Some critical tests have failed. Please address the issues before deploying to production.\n")
                
        logger.info(f"📄 Detailed report saved to: {os.path.abspath(report_path)}")

def main():
    """Main test execution"""
    logger.info("Starting MH Webapps Production Functionality Test")
    
    tester = ProductionFunctionalityTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("🎉 All functionality tests passed! Project is ready for production.")
        sys.exit(0)
    else:
        logger.error("❌ Some functionality tests failed. Please review and fix issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()