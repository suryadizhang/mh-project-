#!/usr/bin/env python3
"""
Comprehensive System Audit for MyHibachi Full Operational Deployment
Analyzes backend, frontend, AI chatbots, and identifies all missing components
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import socket

class MyHibachiSystemAudit:
    """Comprehensive audit of MyHibachi system for operational readiness"""
    
    def __init__(self):
        self.workspace_root = Path("c:/Users/surya/projects/MH webapps")
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "backend_services": {},
            "frontend_apps": {},
            "ai_integration": {},
            "database_systems": {},
            "security_auth": {},
            "production_config": {},
            "missing_components": [],
            "critical_issues": [],
            "recommendations": []
        }
        
    async def run_comprehensive_audit(self):
        """Execute complete system audit"""
        print("🔍 MyHibachi Comprehensive System Audit")
        print("=" * 60)
        print(f"Audit Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Workspace: {self.workspace_root}")
        print()
        
        # Backend Services Audit
        await self.audit_backend_services()
        
        # Frontend Applications Audit
        await self.audit_frontend_applications()
        
        # AI Integration Audit (Critical for your requirements)
        await self.audit_ai_integration()
        
        # Database Systems Audit
        await self.audit_database_systems()
        
        # Security & Authentication Audit
        await self.audit_security_authentication()
        
        # Production Configuration Audit
        await self.audit_production_configuration()
        
        # Generate comprehensive report
        self.generate_audit_report()
        
        # Save detailed results
        self.save_audit_results()
        
    async def audit_backend_services(self):
        """Audit all backend services for operational readiness"""
        print("🔧 Backend Services Audit")
        print("-" * 30)
        
        services = {
            "main_api": {"port": 8003, "path": "apps/api"},
            "ai_api": {"port": 8002, "path": "apps/ai-api"},
        }
        
        backend_results = {}
        
        for service_name, config in services.items():
            print(f"Auditing {service_name}...")
            service_audit = await self.audit_single_service(service_name, config)
            backend_results[service_name] = service_audit
            
            # Check service status
            if service_audit["status"] == "running":
                print(f"  ✅ {service_name}: RUNNING on port {config['port']}")
            else:
                print(f"  ❌ {service_name}: NOT RUNNING")
                self.audit_results["critical_issues"].append(f"{service_name} service not operational")
        
        self.audit_results["backend_services"] = backend_results
        print()
        
    async def audit_single_service(self, service_name: str, config: Dict) -> Dict:
        """Audit a single backend service"""
        service_path = self.workspace_root / config["path"]
        port = config["port"]
        
        audit = {
            "service_name": service_name,
            "port": port,
            "status": "unknown",
            "health_check": False,
            "dependencies": {},
            "configuration": {},
            "api_endpoints": [],
            "issues": []
        }
        
        # Check if service is running
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                audit["status"] = "running"
                audit["health_check"] = True
                audit["health_data"] = response.json()
            else:
                audit["status"] = "unhealthy"
                audit["issues"].append(f"Health check failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            audit["status"] = "not_running"
            audit["issues"].append(f"Connection failed: {str(e)}")
        
        # Check service structure
        if service_path.exists():
            audit["path_exists"] = True
            
            # Check for main.py or app.py
            main_files = list(service_path.glob("**/main.py")) + list(service_path.glob("**/app.py"))
            audit["entry_points"] = [str(f.relative_to(service_path)) for f in main_files]
            
            # Check dependencies
            requirements_file = service_path / "requirements.txt"
            if requirements_file.exists():
                audit["dependencies"]["requirements_txt"] = True
                with open(requirements_file) as f:
                    audit["dependencies"]["packages"] = [line.strip() for line in f if line.strip()]
            
            # Check for environment files
            env_files = list(service_path.glob("**/.env*"))
            audit["configuration"]["env_files"] = [str(f.relative_to(service_path)) for f in env_files]
            
        else:
            audit["path_exists"] = False
            audit["issues"].append(f"Service path does not exist: {service_path}")
        
        return audit
        
    async def audit_frontend_applications(self):
        """Audit frontend applications"""
        print("🌐 Frontend Applications Audit")
        print("-" * 30)
        
        apps = {
            "admin_panel": {"port": 3001, "path": "apps/admin"},
            "customer_app": {"port": 3000, "path": "apps/customer"}
        }
        
        frontend_results = {}
        
        for app_name, config in apps.items():
            print(f"Auditing {app_name}...")
            app_audit = await self.audit_frontend_app(app_name, config)
            frontend_results[app_name] = app_audit
            
            if app_audit["status"] == "running":
                print(f"  ✅ {app_name}: RUNNING on port {config['port']}")
            else:
                print(f"  ❌ {app_name}: NOT RUNNING")
                self.audit_results["critical_issues"].append(f"{app_name} not operational")
        
        self.audit_results["frontend_apps"] = frontend_results
        print()
        
    async def audit_frontend_app(self, app_name: str, config: Dict) -> Dict:
        """Audit a single frontend application"""
        app_path = self.workspace_root / config["path"]
        port = config["port"]
        
        audit = {
            "app_name": app_name,
            "port": port,
            "status": "unknown",
            "accessibility": False,
            "build_system": {},
            "dependencies": {},
            "ai_integration": {},
            "issues": []
        }
        
        # Check if app is accessible
        try:
            response = requests.get(f"http://localhost:{port}", timeout=5)
            if response.status_code == 200:
                audit["status"] = "running"
                audit["accessibility"] = True
            else:
                audit["status"] = "accessible_with_issues"
                audit["issues"].append(f"HTTP status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            audit["status"] = "not_running"
            audit["issues"].append(f"Connection failed: {str(e)}")
        
        # Check app structure
        if app_path.exists():
            audit["path_exists"] = True
            
            # Check package.json
            package_json = app_path / "package.json"
            if package_json.exists():
                audit["build_system"]["package_json"] = True
                try:
                    with open(package_json) as f:
                        package_data = json.load(f)
                        audit["dependencies"]["npm_packages"] = list(package_data.get("dependencies", {}).keys())
                        audit["build_system"]["scripts"] = list(package_data.get("scripts", {}).keys())
                except Exception as e:
                    audit["issues"].append(f"Error reading package.json: {e}")
            
            # Check for AI integration files
            ai_files = []
            ai_files.extend(list(app_path.glob("**/ChatBot.tsx")))
            ai_files.extend(list(app_path.glob("**/ChatWidget.tsx")))
            ai_files.extend(list(app_path.glob("**/ai-api.ts")))
            audit["ai_integration"]["files"] = [str(f.relative_to(app_path)) for f in ai_files]
            
        else:
            audit["path_exists"] = False
            audit["issues"].append(f"App path does not exist: {app_path}")
        
        return audit
        
    async def audit_ai_integration(self):
        """Comprehensive AI integration audit - CRITICAL for your requirements"""
        print("🤖 AI Integration Audit (Customer vs Admin Scope)")
        print("-" * 50)
        
        ai_audit = {
            "ai_api_service": {},
            "customer_ai_scope": {},
            "admin_ai_scope": {},
            "shared_api_architecture": {},
            "permission_separation": {},
            "booking_capabilities": {},
            "admin_management_capabilities": {},
            "scope_compliance": {}
        }
        
        # Check AI API service
        print("Checking AI API service...")
        ai_api_audit = await self.check_ai_api_service()
        ai_audit["ai_api_service"] = ai_api_audit
        
        # Check customer AI scope (booking only)
        print("Analyzing customer AI scope...")
        customer_scope = await self.analyze_customer_ai_scope()
        ai_audit["customer_ai_scope"] = customer_scope
        
        # Check admin AI scope (full management)
        print("Analyzing admin AI scope...")
        admin_scope = await self.analyze_admin_ai_scope()
        ai_audit["admin_ai_scope"] = admin_scope
        
        # Check permission separation
        print("Validating permission separation...")
        permission_audit = await self.validate_ai_permissions()
        ai_audit["permission_separation"] = permission_audit
        
        self.audit_results["ai_integration"] = ai_audit
        
        # Critical checks for your requirements
        self.validate_ai_requirements_compliance(ai_audit)
        print()
        
    async def check_ai_api_service(self) -> Dict:
        """Check AI API service functionality"""
        audit = {
            "service_running": False,
            "endpoints_available": [],
            "websocket_support": False,
            "chat_functionality": False,
            "scope_controls": False,
            "issues": []
        }
        
        try:
            # Check health endpoint
            response = requests.get("http://localhost:8002/health", timeout=5)
            if response.status_code == 200:
                audit["service_running"] = True
                audit["health_data"] = response.json()
            
            # Check chat endpoint
            chat_response = requests.post(
                "http://localhost:8002/api/chat",
                json={"message": "test"},
                timeout=5
            )
            if chat_response.status_code == 200:
                audit["chat_functionality"] = True
                audit["endpoints_available"].append("/api/chat")
            
            # Check WebSocket endpoint (basic connectivity)
            import websockets
            try:
                async with websockets.connect("ws://localhost:8002/ws/chat", timeout=5) as websocket:
                    audit["websocket_support"] = True
            except Exception as ws_error:
                audit["issues"].append(f"WebSocket connection failed: {ws_error}")
                
        except Exception as e:
            audit["issues"].append(f"AI API service check failed: {e}")
            
        return audit
        
    async def analyze_customer_ai_scope(self) -> Dict:
        """Analyze customer AI implementation for booking-only scope"""
        scope_audit = {
            "booking_functions": {
                "create_booking": False,
                "modify_booking": False,
                "cancel_booking": False,
                "view_booking": False
            },
            "restricted_functions": {
                "admin_access": True,  # Should be True (restricted)
                "user_management": True,  # Should be True (restricted)
                "system_config": True,  # Should be True (restricted)
                "financial_data": True  # Should be True (restricted)
            },
            "implementation_found": False,
            "issues": []
        }
        
        # Check customer app ChatWidget implementation
        customer_chat_path = self.workspace_root / "apps/customer/src/components/chat/ChatWidget.tsx"
        if customer_chat_path.exists():
            scope_audit["implementation_found"] = True
            
            # Read the file to analyze scope
            try:
                with open(customer_chat_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for booking-related functionality
                if "booking" in content.lower():
                    scope_audit["booking_functions"]["booking_mentioned"] = True
                if "cancel" in content.lower():
                    scope_audit["booking_functions"]["cancel_booking"] = True
                if "modify" in content.lower() or "update" in content.lower():
                    scope_audit["booking_functions"]["modify_booking"] = True
                    
                # Check for admin function restrictions
                if "admin" in content.lower():
                    scope_audit["issues"].append("Customer AI may have admin function access - SECURITY RISK")
                    scope_audit["restricted_functions"]["admin_access"] = False
                    
            except Exception as e:
                scope_audit["issues"].append(f"Error analyzing customer chat: {e}")
        else:
            scope_audit["issues"].append("Customer ChatWidget not found")
            
        return scope_audit
        
    async def analyze_admin_ai_scope(self) -> Dict:
        """Analyze admin AI implementation for full management scope"""
        scope_audit = {
            "management_functions": {
                "user_management": False,
                "booking_management": False,
                "restaurant_operations": False,
                "financial_oversight": False,
                "system_configuration": False,
                "staff_guidance": False
            },
            "admin_features": {
                "dashboard_integration": False,
                "real_time_chat": False,
                "admin_workflows": False,
                "operational_assistance": False
            },
            "implementation_found": False,
            "issues": []
        }
        
        # Check admin panel ChatBot implementation
        admin_chat_path = self.workspace_root / "apps/admin/src/components/ChatBot.tsx"
        if admin_chat_path.exists():
            scope_audit["implementation_found"] = True
            
            try:
                with open(admin_chat_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for admin-specific features
                if "admin" in content.lower():
                    scope_audit["admin_features"]["dashboard_integration"] = True
                if "websocket" in content.lower() or "ws" in content.lower():
                    scope_audit["admin_features"]["real_time_chat"] = True
                if "management" in content.lower():
                    scope_audit["management_functions"]["booking_management"] = True
                    
                # Check for comprehensive admin capabilities
                admin_keywords = ["user", "staff", "operation", "manage", "configure"]
                for keyword in admin_keywords:
                    if keyword in content.lower():
                        scope_audit["management_functions"][f"{keyword}_mentioned"] = True
                        
            except Exception as e:
                scope_audit["issues"].append(f"Error analyzing admin chat: {e}")
        else:
            scope_audit["issues"].append("Admin ChatBot not found")
            
        return scope_audit
        
    async def validate_ai_permissions(self) -> Dict:
        """Validate AI permission separation between customer and admin"""
        permission_audit = {
            "role_based_access": False,
            "scope_separation": False,
            "api_endpoint_protection": False,
            "context_aware_responses": False,
            "security_implementation": {},
            "issues": []
        }
        
        # Check AI API for role-based logic
        ai_api_path = self.workspace_root / "apps/ai-api"
        
        # Check for role/permission handling in AI service
        service_files = list(ai_api_path.glob("**/*.py"))
        for file_path in service_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if "role" in content.lower() or "permission" in content.lower():
                    permission_audit["role_based_access"] = True
                if "admin" in content.lower() and "customer" in content.lower():
                    permission_audit["scope_separation"] = True
                if "auth" in content.lower() or "token" in content.lower():
                    permission_audit["api_endpoint_protection"] = True
                    
            except Exception as e:
                permission_audit["issues"].append(f"Error reading {file_path}: {e}")
                
        return permission_audit
        
    def validate_ai_requirements_compliance(self, ai_audit: Dict):
        """Validate compliance with specific AI requirements"""
        print("📋 AI Requirements Compliance Check")
        print("-" * 35)
        
        # Customer AI requirements: booking only, no admin functions
        customer_compliance = True
        if not ai_audit["customer_ai_scope"]["booking_functions"].get("booking_mentioned", False):
            self.audit_results["critical_issues"].append("Customer AI missing booking functionality")
            customer_compliance = False
            
        if not ai_audit["customer_ai_scope"]["restricted_functions"].get("admin_access", True):
            self.audit_results["critical_issues"].append("SECURITY: Customer AI has admin access")
            customer_compliance = False
            
        # Admin AI requirements: full management capabilities
        admin_compliance = True
        if not ai_audit["admin_ai_scope"]["implementation_found"]:
            self.audit_results["critical_issues"].append("Admin AI chatbot not implemented")
            admin_compliance = False
            
        if not ai_audit["admin_ai_scope"]["admin_features"].get("real_time_chat", False):
            self.audit_results["critical_issues"].append("Admin AI missing real-time chat")
            admin_compliance = False
            
        # Shared API with different scope requirement
        shared_api_compliance = True
        if not ai_audit["ai_api_service"]["service_running"]:
            self.audit_results["critical_issues"].append("Shared AI API service not running")
            shared_api_compliance = False
            
        if not ai_audit["permission_separation"]["scope_separation"]:
            self.audit_results["critical_issues"].append("AI scope separation not implemented")
            shared_api_compliance = False
            
        print(f"Customer AI Compliance: {'✅' if customer_compliance else '❌'}")
        print(f"Admin AI Compliance: {'✅' if admin_compliance else '❌'}")
        print(f"Shared API Compliance: {'✅' if shared_api_compliance else '❌'}")
        print()
        
    async def audit_database_systems(self):
        """Audit database systems and data integrity"""
        print("🗄️ Database Systems Audit")
        print("-" * 25)
        
        db_audit = {
            "main_database": {},
            "ai_database": {},
            "data_integrity": {},
            "backup_systems": {},
            "issues": []
        }
        
        # Check for database files and configurations
        db_files = list(self.workspace_root.glob("**/*.db"))
        db_audit["database_files"] = [str(f.relative_to(self.workspace_root)) for f in db_files]
        
        # Check database configurations
        env_files = list(self.workspace_root.glob("**/.env*"))
        for env_file in env_files:
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    if "DATABASE_URL" in content:
                        db_audit["database_config_found"] = True
                        break
            except Exception:
                pass
                
        self.audit_results["database_systems"] = db_audit
        print(f"Database files found: {len(db_audit['database_files'])}")
        print()
        
    async def audit_security_authentication(self):
        """Audit security and authentication systems"""
        print("🔒 Security & Authentication Audit")
        print("-" * 35)
        
        security_audit = {
            "authentication_system": {},
            "api_security": {},
            "role_based_access": {},
            "data_protection": {},
            "issues": []
        }
        
        # Check for authentication implementations
        auth_files = []
        for pattern in ["**/auth*", "**/security*", "**/middleware*"]:
            auth_files.extend(list(self.workspace_root.glob(pattern)))
            
        security_audit["auth_files"] = [str(f.relative_to(self.workspace_root)) for f in auth_files]
        
        # Check for JWT or session management
        for service_path in ["apps/api", "apps/ai-api"]:
            service_dir = self.workspace_root / service_path
            if service_dir.exists():
                py_files = list(service_dir.glob("**/*.py"))
                for py_file in py_files:
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "jwt" in content.lower() or "token" in content.lower():
                                security_audit["authentication_system"]["jwt_found"] = True
                            if "middleware" in content.lower():
                                security_audit["api_security"]["middleware_found"] = True
                    except Exception:
                        pass
                        
        self.audit_results["security_auth"] = security_audit
        print(f"Security files found: {len(security_audit['auth_files'])}")
        print()
        
    async def audit_production_configuration(self):
        """Audit production readiness configuration"""
        print("⚙️ Production Configuration Audit")
        print("-" * 35)
        
        prod_audit = {
            "environment_configs": {},
            "deployment_readiness": {},
            "monitoring_logging": {},
            "performance_optimization": {},
            "issues": []
        }
        
        # Check for production configuration files
        config_patterns = ["**/docker*", "**/.env*", "**/nginx*", "**/pm2*", "**/gunicorn*"]
        config_files = []
        for pattern in config_patterns:
            config_files.extend(list(self.workspace_root.glob(pattern)))
            
        prod_audit["config_files"] = [str(f.relative_to(self.workspace_root)) for f in config_files]
        
        # Check for deployment scripts
        deployment_files = list(self.workspace_root.glob("**/deploy*"))
        prod_audit["deployment_files"] = [str(f.relative_to(self.workspace_root)) for f in deployment_files]
        
        self.audit_results["production_config"] = prod_audit
        print(f"Configuration files found: {len(prod_audit['config_files'])}")
        print()
        
    def generate_audit_report(self):
        """Generate comprehensive audit report"""
        print("📊 Comprehensive Audit Report")
        print("=" * 50)
        
        # Calculate overall health scores
        backend_health = self.calculate_backend_health()
        frontend_health = self.calculate_frontend_health()
        ai_health = self.calculate_ai_health()
        overall_health = (backend_health + frontend_health + ai_health) / 3
        
        print(f"Backend Health:     {backend_health:.1f}%")
        print(f"Frontend Health:    {frontend_health:.1f}%")
        print(f"AI Integration:     {ai_health:.1f}%")
        print(f"Overall Health:     {overall_health:.1f}%")
        print()
        
        # Critical issues summary
        if self.audit_results["critical_issues"]:
            print("🚨 Critical Issues Found:")
            for issue in self.audit_results["critical_issues"]:
                print(f"  ❌ {issue}")
            print()
        
        # Generate recommendations
        self.generate_recommendations(overall_health)
        
        # Missing components
        self.identify_missing_components()
        
    def calculate_backend_health(self) -> float:
        """Calculate backend health percentage"""
        backend = self.audit_results["backend_services"]
        if not backend:
            return 0.0
            
        total_checks = 0
        passed_checks = 0
        
        for service, data in backend.items():
            total_checks += 3  # status, health_check, path_exists
            if data.get("status") == "running":
                passed_checks += 1
            if data.get("health_check"):
                passed_checks += 1
            if data.get("path_exists"):
                passed_checks += 1
                
        return (passed_checks / total_checks * 100) if total_checks > 0 else 0.0
        
    def calculate_frontend_health(self) -> float:
        """Calculate frontend health percentage"""
        frontend = self.audit_results["frontend_apps"]
        if not frontend:
            return 0.0
            
        total_checks = 0
        passed_checks = 0
        
        for app, data in frontend.items():
            total_checks += 3  # status, accessibility, path_exists
            if data.get("status") == "running":
                passed_checks += 1
            if data.get("accessibility"):
                passed_checks += 1
            if data.get("path_exists"):
                passed_checks += 1
                
        return (passed_checks / total_checks * 100) if total_checks > 0 else 0.0
        
    def calculate_ai_health(self) -> float:
        """Calculate AI integration health percentage"""
        ai = self.audit_results["ai_integration"]
        if not ai:
            return 0.0
            
        total_checks = 6  # service_running, customer_scope, admin_scope, etc.
        passed_checks = 0
        
        if ai.get("ai_api_service", {}).get("service_running"):
            passed_checks += 1
        if ai.get("customer_ai_scope", {}).get("implementation_found"):
            passed_checks += 1
        if ai.get("admin_ai_scope", {}).get("implementation_found"):
            passed_checks += 1
        if ai.get("ai_api_service", {}).get("chat_functionality"):
            passed_checks += 1
        if ai.get("ai_api_service", {}).get("websocket_support"):
            passed_checks += 1
        if ai.get("permission_separation", {}).get("scope_separation"):
            passed_checks += 1
            
        return (passed_checks / total_checks * 100)
        
    def generate_recommendations(self, overall_health: float):
        """Generate specific recommendations for improvements"""
        recommendations = []
        
        if overall_health < 50:
            recommendations.append("🔴 CRITICAL: System needs major repairs before deployment")
        elif overall_health < 75:
            recommendations.append("🟡 WARNING: Address critical issues before production")
        else:
            recommendations.append("🟢 GOOD: System mostly ready with minor improvements needed")
            
        # Specific AI chatbot recommendations based on your requirements
        ai_data = self.audit_results["ai_integration"]
        
        if not ai_data.get("customer_ai_scope", {}).get("implementation_found"):
            recommendations.append("Implement customer AI chatbot with booking-only scope")
            
        if not ai_data.get("admin_ai_scope", {}).get("implementation_found"):
            recommendations.append("Implement admin AI chatbot with full management capabilities")
            
        if not ai_data.get("permission_separation", {}).get("scope_separation"):
            recommendations.append("CRITICAL: Implement AI scope separation for security")
            
        if not ai_data.get("ai_api_service", {}).get("websocket_support"):
            recommendations.append("Add WebSocket support for real-time AI chat")
            
        self.audit_results["recommendations"] = recommendations
        
        print("💡 Recommendations:")
        for rec in recommendations:
            print(f"  {rec}")
        print()
        
    def identify_missing_components(self):
        """Identify missing components for full operational deployment"""
        missing = []
        
        # Check backend services
        backend = self.audit_results["backend_services"]
        for service_name, data in backend.items():
            if data.get("status") != "running":
                missing.append(f"{service_name} service not operational")
                
        # Check frontend apps
        frontend = self.audit_results["frontend_apps"]
        for app_name, data in frontend.items():
            if data.get("status") != "running":
                missing.append(f"{app_name} not accessible")
                
        # Check AI integration
        ai = self.audit_results["ai_integration"]
        if not ai.get("customer_ai_scope", {}).get("implementation_found"):
            missing.append("Customer AI chatbot implementation")
        if not ai.get("admin_ai_scope", {}).get("implementation_found"):
            missing.append("Admin AI chatbot implementation")
        if not ai.get("permission_separation", {}).get("scope_separation"):
            missing.append("AI role-based access control")
            
        # Check production readiness
        prod = self.audit_results["production_config"]
        if not prod.get("deployment_files"):
            missing.append("Deployment automation scripts")
            
        self.audit_results["missing_components"] = missing
        
        if missing:
            print("📋 Missing Components for Full Deployment:")
            for component in missing:
                print(f"  ⚠️  {component}")
        else:
            print("✅ All core components present")
        print()
        
    def save_audit_results(self):
        """Save detailed audit results to file"""
        results_file = self.workspace_root / "comprehensive_audit_results.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
            print(f"📁 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            
        # Also create a summary report
        self.create_summary_report()
        
    def create_summary_report(self):
        """Create human-readable summary report"""
        summary_file = self.workspace_root / "SYSTEM_AUDIT_SUMMARY.md"
        
        backend_health = self.calculate_backend_health()
        frontend_health = self.calculate_frontend_health()
        ai_health = self.calculate_ai_health()
        overall_health = (backend_health + frontend_health + ai_health) / 3
        
        summary_content = f"""# MyHibachi System Audit Summary

**Audit Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Overall System Health**: {overall_health:.1f}%

## Health Scores
- **Backend Services**: {backend_health:.1f}%
- **Frontend Applications**: {frontend_health:.1f}%
- **AI Integration**: {ai_health:.1f}%

## Critical Issues
{chr(10).join(f'- {issue}' for issue in self.audit_results["critical_issues"]) if self.audit_results["critical_issues"] else "None found"}

## Missing Components
{chr(10).join(f'- {component}' for component in self.audit_results["missing_components"]) if self.audit_results["missing_components"] else "All core components present"}

## Recommendations
{chr(10).join(f'- {rec}' for rec in self.audit_results["recommendations"])}

## Next Steps
1. Address critical issues listed above
2. Implement missing components
3. Follow recommendations for deployment readiness
4. Run final validation before production deployment

---
*Generated by MyHibachi System Audit Tool*
"""
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            print(f"📄 Summary report saved to: {summary_file}")
        except Exception as e:
            print(f"❌ Error saving summary: {e}")


async def main():
    """Run the comprehensive system audit"""
    auditor = MyHibachiSystemAudit()
    await auditor.run_comprehensive_audit()


if __name__ == "__main__":
    print("Starting MyHibachi Comprehensive System Audit...")
    print()
    asyncio.run(main())