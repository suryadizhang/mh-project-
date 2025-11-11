"""
Production Readiness Test Suite
Tests API startup, documentation availability, and basic functionality
"""
import asyncio
import aiohttp
import json
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
import os

class ProductionReadinessTest:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "overall_status": "PENDING",
            "recommendations": []
        }
        self.api_processes = {}
        
    async def test_api_startup(self, api_name: str, port: int, path: str) -> Dict[str, Any]:
        """Test if API can start and respond"""
        result = {
            "can_start": False,
            "responds_to_health": False,
            "startup_time": None,
            "error": None
        }
        
        try:
            # Test health endpoint
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"http://localhost:{port}/health", timeout=5) as response:
                        if response.status == 200:
                            result["can_start"] = True
                            result["responds_to_health"] = True
                            result["startup_time"] = time.time() - start_time
                            health_data = await response.json()
                            result["health_data"] = health_data
                        else:
                            result["error"] = f"Health endpoint returned {response.status}"
                except asyncio.TimeoutError:
                    result["error"] = "Health endpoint timeout"
                except aiohttp.ClientError as e:
                    result["error"] = f"Connection error: {str(e)}"
                    
        except Exception as e:
            result["error"] = f"Startup test failed: {str(e)}"
            
        return result
    
    async def test_api_documentation(self, api_name: str, port: int) -> Dict[str, Any]:
        """Test API documentation endpoints"""
        result = {
            "swagger_available": False,
            "redoc_available": False,
            "openapi_schema": False,
            "schema_valid": False,
            "endpoints_count": 0
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test Swagger UI
                try:
                    async with session.get(f"http://localhost:{port}/docs", timeout=5) as response:
                        if response.status == 200:
                            result["swagger_available"] = True
                except:
                    pass
                
                # Test ReDoc
                try:
                    async with session.get(f"http://localhost:{port}/redoc", timeout=5) as response:
                        if response.status == 200:
                            result["redoc_available"] = True
                except:
                    pass
                
                # Test OpenAPI schema
                try:
                    async with session.get(f"http://localhost:{port}/openapi.json", timeout=5) as response:
                        if response.status == 200:
                            result["openapi_schema"] = True
                            schema_data = await response.json()
                            
                            # Validate schema structure
                            if all(key in schema_data for key in ["openapi", "info", "paths"]):
                                result["schema_valid"] = True
                                result["endpoints_count"] = len(schema_data.get("paths", {}))
                                result["api_title"] = schema_data.get("info", {}).get("title", "Unknown")
                                result["api_version"] = schema_data.get("info", {}).get("version", "Unknown")
                except:
                    pass
                    
        except Exception as e:
            result["error"] = f"Documentation test failed: {str(e)}"
            
        return result
    
    def check_file_structure(self) -> Dict[str, Any]:
        """Check project file structure"""
        result = {
            "operational_api": {},
            "ai_api": {},
            "admin_panel": {},
            "docker": {},
            "environment": {}
        }
        
        # Operational API structure
        op_api_path = Path("apps/api")
        result["operational_api"] = {
            "main_file": (op_api_path / "app" / "main.py").exists(),
            "requirements": (op_api_path / "requirements.txt").exists(),
            "dockerfile": (op_api_path / "Dockerfile").exists(),
            "models": (op_api_path / "app" / "models").exists(),
            "routers": (op_api_path / "app" / "routers").exists(),
            "crm": (op_api_path / "app" / "crm").exists(),
            "alembic": (op_api_path / "alembic.ini").exists()
        }
        
        # AI API structure
        ai_api_path = Path("apps/ai-api")
        result["ai_api"] = {
            "main_file": (ai_api_path / "app" / "main.py").exists(),
            "requirements": (ai_api_path / "requirements.txt").exists(),
            "dockerfile": (ai_api_path / "Dockerfile").exists(),
            "models": (ai_api_path / "app" / "models.py").exists(),
            "services": (ai_api_path / "app" / "services").exists(),
            "routers": (ai_api_path / "app" / "routers").exists()
        }
        
        # Admin panel structure
        admin_path = Path("apps/admin")
        result["admin_panel"] = {
            "package_json": (admin_path / "package.json").exists(),
            "next_config": (admin_path / "next.config.js").exists(),
            "src": (admin_path / "src").exists(),
            "pages": (admin_path / "src" / "app").exists(),
            "components": (admin_path / "src" / "components").exists()
        }
        
        # Docker files
        result["docker"] = {
            "root_dockerfile": Path("Dockerfile").exists(),
            "docker_compose": Path("docker-compose.yml").exists(),
            "api_dockerfile": Path("apps/api/Dockerfile").exists(),
            "ai_api_dockerfile": Path("apps/ai-api/Dockerfile").exists()
        }
        
        # Environment files
        result["environment"] = {
            "api_env": Path("apps/api/.env").exists(),
            "ai_api_env": Path("apps/ai-api/.env").exists(),
            "admin_env": Path("apps/admin/.env.local").exists()
        }
        
        return result
    
    def check_documentation_config(self) -> Dict[str, Any]:
        """Check FastAPI documentation configuration in source files"""
        result = {
            "operational_api": {},
            "ai_api": {}
        }
        
        # Check operational API
        op_main = Path("apps/api/app/main.py")
        if op_main.exists():
            with open(op_main, 'r', encoding='utf-8') as f:
                content = f.read()
                result["operational_api"] = {
                    "fastapi_app": "FastAPI(" in content,
                    "title": "title=" in content,
                    "description": "description=" in content,
                    "version": "version=" in content,
                    "docs_url": "docs_url=" in content,
                    "redoc_url": "redoc_url=" in content,
                    "openapi_url": "openapi_url=" in content
                }
        
        # Check AI API
        ai_main = Path("apps/ai-api/app/main.py")
        if ai_main.exists():
            with open(ai_main, 'r', encoding='utf-8') as f:
                content = f.read()
                result["ai_api"] = {
                    "fastapi_app": "FastAPI(" in content,
                    "title": "title=" in content,
                    "description": "description=" in content,
                    "version": "version=" in content,
                    "docs_url": "docs_url=" in content,
                    "redoc_url": "redoc_url=" in content
                }
        
        return result
    
    async def run_comprehensive_test(self):
        """Run all production readiness tests"""
        print("🚀 Running Comprehensive Production Readiness Test")
        print("=" * 60)
        
        # 1. File Structure Check
        print("📁 Checking file structure...")
        self.results["tests"]["file_structure"] = self.check_file_structure()
        
        # 2. Documentation Configuration Check
        print("📚 Checking documentation configuration...")
        self.results["tests"]["documentation_config"] = self.check_documentation_config()
        
        # 3. API Tests (only test if APIs might be running)
        print("🔌 Testing API endpoints...")
        
        # Test Operational API (port 8003)
        print("  Testing Operational API (port 8003)...")
        self.results["tests"]["operational_api_startup"] = await self.test_api_startup(
            "operational_api", 8003, "apps/api"
        )
        
        if self.results["tests"]["operational_api_startup"]["responds_to_health"]:
            print("  Testing Operational API documentation...")
            self.results["tests"]["operational_api_docs"] = await self.test_api_documentation(
                "operational_api", 8003
            )
        
        # Test AI API (port 8002) 
        print("  Testing AI API (port 8002)...")
        self.results["tests"]["ai_api_startup"] = await self.test_api_startup(
            "ai_api", 8002, "apps/ai-api"
        )
        
        if self.results["tests"]["ai_api_startup"]["responds_to_health"]:
            print("  Testing AI API documentation...")
            self.results["tests"]["ai_api_docs"] = await self.test_api_documentation(
                "ai_api", 8002
            )
        
        # 4. Generate Recommendations
        self.generate_recommendations()
        
        # 5. Calculate Overall Status
        self.calculate_overall_status()
        
        # 6. Print Results
        self.print_results()
        
        # 7. Save Results
        with open("production_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        return self.results
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # File structure recommendations
        file_results = self.results["tests"]["file_structure"]
        for component, files in file_results.items():
            missing_files = [k for k, v in files.items() if not v]
            if missing_files:
                recommendations.append(f"Missing {component} files: {', '.join(missing_files)}")
        
        # API startup recommendations
        if not self.results["tests"]["operational_api_startup"]["responds_to_health"]:
            recommendations.append("Operational API (port 8003) is not responding - check startup and environment variables")
        
        if not self.results["tests"]["ai_api_startup"]["responds_to_health"]:
            recommendations.append("AI API (port 8002) is not responding - check startup and OpenAI API key")
        
        # Documentation recommendations
        doc_config = self.results["tests"]["documentation_config"]
        for api_name, config in doc_config.items():
            missing_config = [k for k, v in config.items() if not v]
            if missing_config:
                recommendations.append(f"{api_name} missing documentation config: {', '.join(missing_config)}")
        
        # General production recommendations
        recommendations.extend([
            "Start both APIs: uvicorn app.main:app --host 0.0.0.0 --port 8003 (operational) and --port 8002 (AI)",
            "Verify all environment variables are set correctly",
            "Test all API endpoints using Swagger UI at /docs",
            "Run frontend tests against both APIs",
            "Set up SSL certificates for production deployment",
            "Configure database backups and monitoring",
            "Implement automated testing in CI/CD pipeline"
        ])
        
        self.results["recommendations"] = recommendations
    
    def calculate_overall_status(self):
        """Calculate overall production readiness status"""
        file_structure_ok = all(
            all(files.values()) for files in self.results["tests"]["file_structure"].values()
        )
        
        docs_config_ok = all(
            all(config.values()) for config in self.results["tests"]["documentation_config"].values()
        )
        
        apis_responding = (
            self.results["tests"]["operational_api_startup"]["responds_to_health"] and
            self.results["tests"]["ai_api_startup"]["responds_to_health"]
        )
        
        if file_structure_ok and docs_config_ok and apis_responding:
            self.results["overall_status"] = "READY_FOR_PRODUCTION"
        elif file_structure_ok and docs_config_ok:
            self.results["overall_status"] = "READY_FOR_TESTING"
        else:
            self.results["overall_status"] = "NEEDS_SETUP"
    
    def print_results(self):
        """Print formatted test results"""
        print("\n" + "=" * 60)
        print(f"📊 OVERALL STATUS: {self.results['overall_status']}")
        print("=" * 60)
        
        # File Structure Results
        print("\n📁 FILE STRUCTURE:")
        for component, files in self.results["tests"]["file_structure"].items():
            all_present = all(files.values())
            status = "✅" if all_present else "❌"
            print(f"  {status} {component.upper()}")
            for file_name, exists in files.items():
                icon = "✅" if exists else "❌"
                print(f"    {icon} {file_name}")
        
        # Documentation Config Results
        print("\n📚 DOCUMENTATION CONFIG:")
        for api_name, config in self.results["tests"]["documentation_config"].items():
            all_configured = all(config.values())
            status = "✅" if all_configured else "❌"
            print(f"  {status} {api_name.upper()}")
            for config_name, configured in config.items():
                icon = "✅" if configured else "❌"
                print(f"    {icon} {config_name}")
        
        # API Status Results
        print("\n🔌 API STATUS:")
        
        # Operational API
        op_startup = self.results["tests"]["operational_api_startup"]
        op_status = "✅" if op_startup["responds_to_health"] else "❌"
        print(f"  {op_status} Operational API (port 8003)")
        if op_startup["responds_to_health"]:
            print(f"    ✅ Health check: {op_startup.get('startup_time', 0):.2f}s")
            if "operational_api_docs" in self.results["tests"]:
                docs = self.results["tests"]["operational_api_docs"]
                print(f"    {'✅' if docs['swagger_available'] else '❌'} Swagger UI available")
                print(f"    {'✅' if docs['openapi_schema'] else '❌'} OpenAPI schema")
                if docs.get('endpoints_count', 0) > 0:
                    print(f"    📊 {docs['endpoints_count']} endpoints documented")
        else:
            print(f"    ❌ Error: {op_startup.get('error', 'Unknown')}")
        
        # AI API
        ai_startup = self.results["tests"]["ai_api_startup"]
        ai_status = "✅" if ai_startup["responds_to_health"] else "❌"
        print(f"  {ai_status} AI API (port 8002)")
        if ai_startup["responds_to_health"]:
            print(f"    ✅ Health check: {ai_startup.get('startup_time', 0):.2f}s")
            if "ai_api_docs" in self.results["tests"]:
                docs = self.results["tests"]["ai_api_docs"]
                print(f"    {'✅' if docs['swagger_available'] else '❌'} Swagger UI available")
                print(f"    {'✅' if docs['openapi_schema'] else '❌'} OpenAPI schema")
                if docs.get('endpoints_count', 0) > 0:
                    print(f"    📊 {docs['endpoints_count']} endpoints documented")
        else:
            print(f"    ❌ Error: {ai_startup.get('error', 'Unknown')}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(self.results["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n📄 Detailed results saved to: production_test_results.json")
        print("=" * 60)


async def main():
    """Main test runner"""
    tester = ProductionReadinessTest()
    results = await tester.run_comprehensive_test()
    return results

if __name__ == "__main__":
    asyncio.run(main())