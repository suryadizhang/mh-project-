#!/usr/bin/env python3
"""
Production Readiness Assessment Script for MyHibachi
Comprehensive check for deployment readiness and best practices
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
import subprocess
import importlib.util

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionReadinessChecker:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {}
        self.issues = []
        self.warnings = []
        self.passed_checks = []
        
    def log_check(self, check_name: str, status: str, message: str, severity: str = "info"):
        """Log a check result"""
        result = {
            "check": check_name,
            "status": status,
            "message": message,
            "severity": severity,
            "timestamp": time.time()
        }
        
        self.results[check_name] = result
        
        if status == "PASS":
            self.passed_checks.append(result)
            logger.info(f"✅ {check_name}: {message}")
        elif status == "WARN":
            self.warnings.append(result)
            logger.warning(f"⚠️ {check_name}: {message}")
        elif status == "FAIL":
            self.issues.append(result)
            logger.error(f"❌ {check_name}: {message}")
        else:
            logger.info(f"ℹ️ {check_name}: {message}")

    def check_environment_variables(self) -> Dict[str, Any]:
        """Check if all required environment variables are properly configured"""
        logger.info("🔍 Checking environment variables...")
        
        # Required environment variables for production
        required_vars = {
            'api': [
                'SECRET_KEY',
                'DATABASE_URL', 
                'STRIPE_SECRET_KEY',
                'STRIPE_WEBHOOK_SECRET',
                'SMTP_HOST',
                'SMTP_USER',
                'SMTP_PASSWORD'
            ],
            'customer': [
                'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY',
                'NEXTAUTH_SECRET',
                'NEXTAUTH_URL',
                'NEXT_PUBLIC_API_URL'
            ],
            'admin': [
                'NEXT_PUBLIC_API_URL',
                'NEXTAUTH_SECRET',
                'NEXTAUTH_URL'
            ]
        }

        apps_to_check = ['api', 'customer', 'admin']
        env_status = {}
        
        for app in apps_to_check:
            app_path = self.project_root / 'apps' / app
            env_file = app_path / '.env'
            env_example = app_path / '.env.example'
            
            env_status[app] = {
                'env_file_exists': env_file.exists(),
                'env_example_exists': env_example.exists(),
                'missing_vars': [],
                'insecure_vars': []
            }
            
            if not env_file.exists():
                self.log_check(f"Environment File - {app}", "FAIL", 
                             f"Missing .env file in {app} directory", "critical")
                continue
                
            # Read .env file
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                    
                # Check required variables
                for var in required_vars.get(app, []):
                    if f"{var}=" not in env_content:
                        env_status[app]['missing_vars'].append(var)
                        
                # Check for insecure default values
                insecure_patterns = [
                    'your-secret-key-here',
                    'change-me',
                    'your_api_key_here',
                    'localhost:3000',  # in production URLs
                    'test_key',
                    'development_secret'
                ]
                
                for pattern in insecure_patterns:
                    if pattern in env_content.lower():
                        env_status[app]['insecure_vars'].append(pattern)
                        
            except Exception as e:
                self.log_check(f"Environment File - {app}", "FAIL", 
                             f"Error reading .env file: {str(e)}", "critical")
                continue
                
            # Report results
            if env_status[app]['missing_vars']:
                self.log_check(f"Environment Variables - {app}", "FAIL",
                             f"Missing required variables: {', '.join(env_status[app]['missing_vars'])}", "critical")
            else:
                self.log_check(f"Environment Variables - {app}", "PASS",
                             "All required environment variables present")
                             
            if env_status[app]['insecure_vars']:
                self.log_check(f"Environment Security - {app}", "WARN",
                             f"Insecure default values found: {', '.join(env_status[app]['insecure_vars'])}", "high")
            else:
                self.log_check(f"Environment Security - {app}", "PASS",
                             "No insecure default values detected")
        
        return env_status

    def check_database_configuration(self) -> Dict[str, Any]:
        """Check database configuration and connectivity"""
        logger.info("🗄️ Checking database configuration...")
        
        db_status = {
            'migrations_exist': False,
            'alembic_configured': False,
            'connection_testable': False
        }
        
        # Check for Alembic migrations
        api_path = self.project_root / 'apps' / 'api'
        alembic_dir = api_path / 'alembic'
        alembic_ini = api_path / 'alembic.ini'
        
        if alembic_dir.exists() and alembic_ini.exists():
            db_status['alembic_configured'] = True
            self.log_check("Database Migrations", "PASS", "Alembic migrations configured")
            
            # Check if there are migration files
            versions_dir = alembic_dir / 'versions'
            if versions_dir.exists():
                migration_files = list(versions_dir.glob('*.py'))
                if migration_files:
                    db_status['migrations_exist'] = True
                    self.log_check("Migration Files", "PASS", 
                                 f"Found {len(migration_files)} migration files")
                else:
                    self.log_check("Migration Files", "WARN", 
                                 "No migration files found", "medium")
            else:
                self.log_check("Migration Files", "WARN", 
                             "No versions directory found", "medium")
        else:
            self.log_check("Database Migrations", "FAIL", 
                         "Alembic not configured", "high")
        
        # Check for database models
        models_dir = api_path / 'app' / 'models'
        if models_dir.exists():
            model_files = list(models_dir.glob('*.py'))
            if model_files:
                self.log_check("Database Models", "PASS", 
                             f"Found {len(model_files)} model files")
            else:
                self.log_check("Database Models", "WARN", 
                             "No model files found", "medium")
        else:
            self.log_check("Database Models", "FAIL", 
                         "Models directory not found", "high")
            
        return db_status

    def check_security_configuration(self) -> Dict[str, Any]:
        """Check security configurations and best practices"""
        logger.info("🔐 Checking security configuration...")
        
        security_status = {
            'cors_configured': False,
            'rate_limiting': False,
            'https_enforced': False,
            'auth_configured': False
        }
        
        # Check API security configuration
        api_main = self.project_root / 'apps' / 'api' / 'app' / 'main.py'
        if api_main.exists():
            try:
                with open(api_main, 'r') as f:
                    content = f.read()
                    
                # Check CORS configuration
                if 'CORSMiddleware' in content:
                    security_status['cors_configured'] = True
                    self.log_check("CORS Configuration", "PASS", "CORS middleware configured")
                else:
                    self.log_check("CORS Configuration", "FAIL", 
                                 "CORS middleware not found", "high")
                
                # Check rate limiting
                if 'rate_limit' in content.lower() or 'limiter' in content.lower():
                    security_status['rate_limiting'] = True
                    self.log_check("Rate Limiting", "PASS", "Rate limiting configured")
                else:
                    self.log_check("Rate Limiting", "WARN", 
                                 "Rate limiting not detected", "medium")
                    
                # Check authentication setup
                if 'auth' in content.lower() and ('jwt' in content.lower() or 'oauth' in content.lower()):
                    security_status['auth_configured'] = True
                    self.log_check("Authentication", "PASS", "Authentication configured")
                else:
                    self.log_check("Authentication", "WARN", 
                                 "Authentication setup not clear", "high")
                    
            except Exception as e:
                self.log_check("Security Check", "FAIL", 
                             f"Error reading main.py: {str(e)}", "high")
        
        # Check for security middleware
        middleware_dir = self.project_root / 'apps' / 'api' / 'app' / 'middleware'
        if middleware_dir.exists():
            middleware_files = list(middleware_dir.glob('*.py'))
            if middleware_files:
                self.log_check("Security Middleware", "PASS", 
                             f"Found {len(middleware_files)} middleware files")
            else:
                self.log_check("Security Middleware", "WARN", 
                             "No middleware files found", "medium")
        
        return security_status

    def check_testing_infrastructure(self) -> Dict[str, Any]:
        """Check testing setup and coverage"""
        logger.info("🧪 Checking testing infrastructure...")
        
        test_status = {
            'unit_tests_exist': False,
            'e2e_tests_exist': False,
            'test_config': False,
            'ci_config': False
        }
        
        # Check for unit tests
        apps_to_check = ['api', 'customer', 'admin']
        for app in apps_to_check:
            test_dir = self.project_root / 'apps' / app / 'tests'
            test_files = []
            
            if test_dir.exists():
                test_files = list(test_dir.glob('test_*.py')) + list(test_dir.glob('*_test.py'))
                if test_files:
                    test_status['unit_tests_exist'] = True
                    self.log_check(f"Unit Tests - {app}", "PASS", 
                                 f"Found {len(test_files)} test files")
                else:
                    self.log_check(f"Unit Tests - {app}", "WARN", 
                                 "No unit test files found", "medium")
            else:
                # Check for test files in src directory
                if app in ['customer', 'admin']:
                    src_tests = self.project_root / 'apps' / app / 'src' / 'test'
                    if src_tests.exists():
                        test_files = list(src_tests.glob('*.test.*'))
                        if test_files:
                            test_status['unit_tests_exist'] = True
                            self.log_check(f"Unit Tests - {app}", "PASS", 
                                         f"Found {len(test_files)} test files in src")
                        else:
                            self.log_check(f"Unit Tests - {app}", "WARN", 
                                         "No test files found", "medium")
                    else:
                        self.log_check(f"Unit Tests - {app}", "WARN", 
                                     "No test directory found", "medium")
        
        # Check for E2E tests
        e2e_dir = self.project_root / 'e2e'
        if e2e_dir.exists():
            e2e_files = list(e2e_dir.rglob('*.spec.*')) + list(e2e_dir.rglob('*.test.*'))
            if e2e_files:
                test_status['e2e_tests_exist'] = True
                self.log_check("E2E Tests", "PASS", 
                             f"Found {len(e2e_files)} E2E test files")
            else:
                self.log_check("E2E Tests", "WARN", 
                             "No E2E test files found", "medium")
        else:
            self.log_check("E2E Tests", "WARN", 
                         "No E2E test directory found", "medium")
        
        # Check for test configuration
        playwright_config = self.project_root / 'playwright.config.ts'
        if playwright_config.exists():
            test_status['test_config'] = True
            self.log_check("Test Configuration", "PASS", "Playwright config found")
        
        # Check for CI configuration
        ci_configs = [
            self.project_root / '.github' / 'workflows',
            self.project_root / '.gitlab-ci.yml',
            self.project_root / 'azure-pipelines.yml'
        ]
        
        for ci_config in ci_configs:
            if ci_config.exists():
                test_status['ci_config'] = True
                self.log_check("CI Configuration", "PASS", f"CI config found: {ci_config.name}")
                break
        else:
            self.log_check("CI Configuration", "WARN", 
                         "No CI configuration found", "medium")
        
        return test_status

    def check_api_documentation(self) -> Dict[str, Any]:
        """Check API documentation completeness"""
        logger.info("📚 Checking API documentation...")
        
        docs_status = {
            'openapi_configured': False,
            'readme_exists': False,
            'api_docs_exist': False
        }
        
        # Check for OpenAPI/Swagger configuration
        api_main = self.project_root / 'apps' / 'api' / 'app' / 'main.py'
        if api_main.exists():
            try:
                with open(api_main, 'r') as f:
                    content = f.read()
                    if 'docs_url' in content or 'openapi' in content:
                        docs_status['openapi_configured'] = True
                        self.log_check("OpenAPI Configuration", "PASS", 
                                     "OpenAPI/Swagger documentation configured")
                    else:
                        self.log_check("OpenAPI Configuration", "WARN", 
                                     "OpenAPI documentation not configured", "medium")
            except Exception as e:
                self.log_check("OpenAPI Configuration", "FAIL", 
                             f"Error checking main.py: {str(e)}", "medium")
        
        # Check for API documentation files
        api_docs = [
            self.project_root / 'apps' / 'api' / 'API_DOCUMENTATION.md',
            self.project_root / 'apps' / 'api' / 'README.md',
            self.project_root / 'docs' / 'api.md'
        ]
        
        for doc_file in api_docs:
            if doc_file.exists():
                docs_status['api_docs_exist'] = True
                self.log_check("API Documentation", "PASS", 
                             f"API documentation found: {doc_file.name}")
                break
        else:
            self.log_check("API Documentation", "WARN", 
                         "No API documentation files found", "medium")
        
        # Check for README files
        readme_files = [
            self.project_root / 'README.md',
            self.project_root / 'apps' / 'api' / 'README.md'
        ]
        
        for readme in readme_files:
            if readme.exists():
                docs_status['readme_exists'] = True
                self.log_check("README Documentation", "PASS", 
                             f"README found: {readme.name}")
                break
        else:
            self.log_check("README Documentation", "WARN", 
                         "No README files found", "low")
        
        return docs_status

    def check_deployment_configuration(self) -> Dict[str, Any]:
        """Check deployment readiness"""
        logger.info("🚀 Checking deployment configuration...")
        
        deploy_status = {
            'dockerfile_exists': False,
            'docker_compose_exists': False,
            'deployment_scripts': False,
            'production_config': False
        }
        
        # Check for Dockerfile
        dockerfiles = [
            self.project_root / 'Dockerfile',
            self.project_root / 'apps' / 'api' / 'Dockerfile',
            self.project_root / 'apps' / 'customer' / 'Dockerfile'
        ]
        
        for dockerfile in dockerfiles:
            if dockerfile.exists():
                deploy_status['dockerfile_exists'] = True
                self.log_check("Docker Configuration", "PASS", 
                             f"Dockerfile found: {dockerfile}")
                break
        else:
            self.log_check("Docker Configuration", "WARN", 
                         "No Dockerfile found", "medium")
        
        # Check for docker-compose
        compose_files = [
            self.project_root / 'docker-compose.yml',
            self.project_root / 'docker-compose.prod.yml'
        ]
        
        for compose_file in compose_files:
            if compose_file.exists():
                deploy_status['docker_compose_exists'] = True
                self.log_check("Docker Compose", "PASS", 
                             f"Docker Compose found: {compose_file.name}")
                break
        else:
            self.log_check("Docker Compose", "WARN", 
                         "No Docker Compose configuration found", "low")
        
        # Check for deployment scripts
        deploy_scripts = [
            self.project_root / 'deploy.sh',
            self.project_root / 'scripts' / 'deploy.sh',
            self.project_root / 'deployment',
        ]
        
        for script in deploy_scripts:
            if script.exists():
                deploy_status['deployment_scripts'] = True
                self.log_check("Deployment Scripts", "PASS", 
                             f"Deployment script found: {script.name}")
                break
        else:
            self.log_check("Deployment Scripts", "WARN", 
                         "No deployment scripts found", "low")
        
        return deploy_status

    def check_monitoring_and_logging(self) -> Dict[str, Any]:
        """Check monitoring and logging setup"""
        logger.info("📊 Checking monitoring and logging...")
        
        monitoring_status = {
            'logging_configured': False,
            'metrics_configured': False,
            'health_checks': False,
            'error_tracking': False
        }
        
        # Check logging configuration
        api_main = self.project_root / 'apps' / 'api' / 'app' / 'main.py'
        if api_main.exists():
            try:
                with open(api_main, 'r') as f:
                    content = f.read()
                    if 'logging' in content:
                        monitoring_status['logging_configured'] = True
                        self.log_check("Logging Configuration", "PASS", 
                                     "Logging configured in API")
                    else:
                        self.log_check("Logging Configuration", "WARN", 
                                     "Logging not configured", "medium")
                        
                    # Check for metrics
                    if 'prometheus' in content.lower() or 'metrics' in content.lower():
                        monitoring_status['metrics_configured'] = True
                        self.log_check("Metrics Configuration", "PASS", 
                                     "Metrics collection configured")
                    else:
                        self.log_check("Metrics Configuration", "WARN", 
                                     "Metrics collection not configured", "low")
                        
            except Exception as e:
                self.log_check("Monitoring Check", "FAIL", 
                             f"Error checking main.py: {str(e)}", "medium")
        
        # Check for health check endpoints
        health_router = self.project_root / 'apps' / 'api' / 'app' / 'routers' / 'health.py'
        if health_router.exists():
            monitoring_status['health_checks'] = True
            self.log_check("Health Checks", "PASS", "Health check endpoints found")
        else:
            self.log_check("Health Checks", "WARN", 
                         "No health check endpoints found", "medium")
        
        return monitoring_status

    def run_dependency_check(self) -> Dict[str, Any]:
        """Check for outdated or vulnerable dependencies"""
        logger.info("📦 Checking dependencies...")
        
        dep_status = {
            'package_files_exist': False,
            'lockfiles_exist': False,
            'vulnerabilities_checked': False
        }
        
        # Check for package files
        package_files = [
            self.project_root / 'package.json',
            self.project_root / 'apps' / 'api' / 'requirements.txt',
            self.project_root / 'apps' / 'api' / 'pyproject.toml',
            self.project_root / 'apps' / 'customer' / 'package.json'
        ]
        
        existing_package_files = [f for f in package_files if f.exists()]
        if existing_package_files:
            dep_status['package_files_exist'] = True
            self.log_check("Package Files", "PASS", 
                         f"Found {len(existing_package_files)} package files")
        else:
            self.log_check("Package Files", "FAIL", 
                         "No package files found", "critical")
        
        # Check for lock files
        lock_files = [
            self.project_root / 'package-lock.json',
            self.project_root / 'apps' / 'customer' / 'package-lock.json',
            self.project_root / 'apps' / 'admin' / 'package-lock.json'
        ]
        
        existing_lock_files = [f for f in lock_files if f.exists()]
        if existing_lock_files:
            dep_status['lockfiles_exist'] = True
            self.log_check("Lock Files", "PASS", 
                         f"Found {len(existing_lock_files)} lock files")
        else:
            self.log_check("Lock Files", "WARN", 
                         "No lock files found - dependency versions not pinned", "medium")
        
        return dep_status

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness report"""
        total_checks = len(self.results)
        passed = len(self.passed_checks)
        warnings = len(self.warnings)
        failures = len(self.issues)
        
        # Calculate readiness score
        score = (passed / total_checks * 100) if total_checks > 0 else 0
        
        # Determine readiness level
        if score >= 90 and failures == 0:
            readiness_level = "PRODUCTION_READY"
        elif score >= 80 and failures <= 2:
            readiness_level = "MOSTLY_READY"
        elif score >= 60:
            readiness_level = "NEEDS_WORK"
        else:
            readiness_level = "NOT_READY"
        
        report = {
            "timestamp": time.time(),
            "project_root": str(self.project_root),
            "readiness_level": readiness_level,
            "score": round(score, 2),
            "summary": {
                "total_checks": total_checks,
                "passed": passed,
                "warnings": warnings,
                "failures": failures
            },
            "results": self.results,
            "critical_issues": [issue for issue in self.issues if issue["severity"] == "critical"],
            "high_priority_issues": [issue for issue in self.issues if issue["severity"] == "high"],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on check results"""
        recommendations = []
        
        if len(self.issues) > 0:
            recommendations.append("Address all critical and high-severity issues before production deployment")
        
        if any("Environment" in issue["check"] for issue in self.issues):
            recommendations.append("Complete environment variable configuration with secure values")
        
        if any("Security" in issue["check"] for issue in self.issues):
            recommendations.append("Implement comprehensive security measures including HTTPS, rate limiting, and input validation")
        
        if any("Test" in issue["check"] for issue in self.warnings):
            recommendations.append("Increase test coverage with unit tests, integration tests, and E2E tests")
        
        if any("Database" in issue["check"] for issue in self.issues):
            recommendations.append("Set up proper database migrations and backup strategies")
        
        if any("Documentation" in issue["check"] for issue in self.warnings):
            recommendations.append("Complete API documentation and deployment guides")
        
        if any("Monitoring" in issue["check"] for issue in self.warnings):
            recommendations.append("Implement monitoring, logging, and alerting systems")
        
        return recommendations

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all production readiness checks"""
        logger.info("🚀 Starting Production Readiness Assessment for MyHibachi")
        
        checks = [
            self.check_environment_variables,
            self.check_database_configuration,
            self.check_security_configuration,
            self.check_testing_infrastructure,
            self.check_api_documentation,
            self.check_deployment_configuration,
            self.check_monitoring_and_logging,
            self.run_dependency_check
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                logger.error(f"❌ Error running {check.__name__}: {str(e)}")
                self.log_check(check.__name__, "FAIL", f"Check failed with error: {str(e)}", "critical")
        
        return self.generate_report()


async def main():
    """Main function to run production readiness assessment"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    checker = ProductionReadinessChecker(project_root)
    report = await checker.run_all_checks()
    
    # Save report to file
    report_file = os.path.join(project_root, 'production_readiness_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("🏁 PRODUCTION READINESS ASSESSMENT COMPLETE")
    print("="*80)
    print(f"📊 Overall Score: {report['score']}%")
    print(f"🚦 Readiness Level: {report['readiness_level']}")
    print(f"✅ Passed: {report['summary']['passed']}")
    print(f"⚠️ Warnings: {report['summary']['warnings']}")
    print(f"❌ Failures: {report['summary']['failures']}")
    
    if report['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES ({len(report['critical_issues'])}):")
        for issue in report['critical_issues']:
            print(f"   • {issue['check']}: {issue['message']}")
    
    if report['high_priority_issues']:
        print(f"\n⚠️ HIGH PRIORITY ISSUES ({len(report['high_priority_issues'])}):")
        for issue in report['high_priority_issues']:
            print(f"   • {issue['check']}: {issue['message']}")
    
    if report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print("="*80)
    
    # Exit with appropriate code
    if report['readiness_level'] in ['PRODUCTION_READY', 'MOSTLY_READY']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())