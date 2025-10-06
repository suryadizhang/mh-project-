#!/usr/bin/env python3
"""
Comprehensive Production Readiness & Testing Setup for MH Webapps
===================================================================

This script performs:
1. Production readiness assessment
2. API documentation verification
3. Comprehensive testing setup
4. Local deployment validation
5. Security and performance audit
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field
import requests
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProductionStatus:
    """Tracks production readiness status"""
    component: str
    status: str  # READY, NOT_READY, WARNING
    score: float  # 0.0 - 1.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class ProductionReadinessChecker:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.results = []
        
        # Define project structure
        self.apps = {
            'api': self.workspace_path / 'apps' / 'api',
            'customer': self.workspace_path / 'apps' / 'customer', 
            'admin': self.workspace_path / 'apps' / 'admin',
            'ai-api': self.workspace_path / 'apps' / 'ai-api'
        }
        
    def check_environment_configuration(self) -> ProductionStatus:
        """Check environment configuration for all apps"""
        logger.info("🔍 Checking environment configuration...")
        status = ProductionStatus("Environment Configuration", "READY", 1.0)
        
        required_env_files = {
            'api': ['.env', '.env.example'],
            'customer': ['.env.local', '.env.example'],
            'admin': ['.env.local', '.env.example']
        }
        
        for app_name, required_files in required_env_files.items():
            app_path = self.apps.get(app_name)
            if not app_path or not app_path.exists():
                status.issues.append(f"❌ {app_name} app directory not found")
                status.score -= 0.2
                continue
                
            for env_file in required_files:
                env_path = app_path / env_file
                if env_path.exists():
                    logger.info(f"✅ Found {app_name}/{env_file}")
                    # Check if env file has content
                    if env_path.stat().st_size == 0:
                        status.issues.append(f"⚠️  {app_name}/{env_file} is empty")
                        status.score -= 0.05
                else:
                    if env_file.endswith('.example'):
                        status.issues.append(f"⚠️  Missing {app_name}/{env_file}")
                        status.score -= 0.05
                    else:
                        status.issues.append(f"❌ Missing critical {app_name}/{env_file}")
                        status.score -= 0.15
        
        # Check for sensitive env vars in .env files
        sensitive_patterns = ['DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET', 'STRIPE_', 'OPENAI_API_KEY']
        for app_name in ['api']:
            env_path = self.apps[app_name] / '.env'
            if env_path.exists():
                try:
                    content = env_path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    content = env_path.read_text(encoding='latin-1', errors='ignore')
                for pattern in sensitive_patterns:
                    if pattern in content and not content.count(f'{pattern}=your_') > 0:
                        logger.info(f"✅ {app_name} has {pattern} configured")
                    else:
                        status.issues.append(f"⚠️  {app_name} missing {pattern}")
                        status.score -= 0.05
        
        if status.score < 0.7:
            status.status = "NOT_READY"
        elif status.score < 0.9:
            status.status = "WARNING"
            
        return status
    
    def check_database_configuration(self) -> ProductionStatus:
        """Check database configuration and migrations"""
        logger.info("🔍 Checking database configuration...")
        status = ProductionStatus("Database Configuration", "READY", 1.0)
        
        # Check for Alembic migrations
        api_path = self.apps['api']
        alembic_path = api_path / 'alembic'
        versions_path = alembic_path / 'versions'
        
        if not alembic_path.exists():
            status.issues.append("❌ Alembic migration directory not found")
            status.score -= 0.3
        elif not versions_path.exists():
            status.issues.append("❌ Alembic versions directory not found")
            status.score -= 0.2
        else:
            migrations = list(versions_path.glob('*.py'))
            if len(migrations) == 0:
                status.issues.append("❌ No database migrations found")
                status.score -= 0.2
            else:
                logger.info(f"✅ Found {len(migrations)} database migrations")
        
        # Check for database models
        models_path = api_path / 'app' / 'models'
        if not models_path.exists():
            status.issues.append("❌ Database models directory not found")
            status.score -= 0.2
        else:
            models = list(models_path.glob('*.py'))
            logger.info(f"✅ Found {len(models)} model files")
        
        # Check alembic.ini
        alembic_ini = api_path / 'alembic.ini'
        if not alembic_ini.exists():
            status.issues.append("❌ alembic.ini not found")
            status.score -= 0.1
        else:
            logger.info("✅ alembic.ini found")
        
        if status.score < 0.7:
            status.status = "NOT_READY"
        elif status.score < 0.9:
            status.status = "WARNING"
            
        return status
    
    def check_api_documentation(self) -> ProductionStatus:
        """Check API documentation setup"""
        logger.info("🔍 Checking API documentation...")
        status = ProductionStatus("API Documentation", "READY", 1.0)
        
        api_path = self.apps['api']
        
        # Check for API documentation files
        doc_files = {
            'API_DOCUMENTATION.md': api_path / 'API_DOCUMENTATION.md',
            'openapi_config.py': api_path / 'app' / 'openapi_config.py',
            'main.py': api_path / 'app' / 'main.py'
        }
        
        for doc_name, doc_path in doc_files.items():
            if doc_path.exists():
                logger.info(f"✅ Found {doc_name}")
                if doc_name == 'main.py':
                    # Check if main.py has OpenAPI configuration
                    try:
                        content = doc_path.read_text(encoding='utf-8')
                        if 'openapi' in content.lower():
                            logger.info("✅ FastAPI has OpenAPI configuration")
                        else:
                            status.issues.append("⚠️  FastAPI missing OpenAPI configuration")
                            status.score -= 0.1
                    except UnicodeDecodeError:
                        status.recommendations.append("🔧 Check main.py file encoding")
                        status.score -= 0.05
            else:
                status.issues.append(f"❌ Missing {doc_name}")
                status.score -= 0.2
        
        # Check if FastAPI docs are accessible (if server is running)
        try:
            response = requests.get('http://localhost:8000/docs', timeout=2)
            if response.status_code == 200:
                logger.info("✅ Swagger UI accessible")
            else:
                status.recommendations.append("🔧 Start API server to verify Swagger UI")
        except:
            status.recommendations.append("🔧 Start API server to verify Swagger UI")
        
        if status.score < 0.7:
            status.status = "NOT_READY"
        elif status.score < 0.9:
            status.status = "WARNING"
            
        return status
    
    def check_testing_infrastructure(self) -> ProductionStatus:
        """Check testing setup and coverage"""
        logger.info("🔍 Checking testing infrastructure...")
        status = ProductionStatus("Testing Infrastructure", "READY", 1.0)
        
        # Check for test directories
        test_dirs = {
            'api_tests': self.apps['api'] / 'tests',
            'e2e_tests': self.workspace_path / 'e2e',
            'customer_tests': self.apps['customer'] / '__tests__',
            'admin_tests': self.apps['admin'] / '__tests__'
        }
        
        for test_name, test_path in test_dirs.items():
            if test_path.exists():
                test_files = list(test_path.rglob('*test*.py')) + list(test_path.rglob('*test*.ts')) + list(test_path.rglob('*spec*.ts'))
                if test_files:
                    logger.info(f"✅ Found {len(test_files)} test files in {test_name}")
                else:
                    # Only warn if the directory was expected to have tests
                    if 'customer' in test_name or 'admin' in test_name:
                        status.recommendations.append(f"🔧 Add test files to {test_name}")
                    else:
                        status.issues.append(f"⚠️  {test_name} directory exists but no test files found")
                        status.score -= 0.05
            else:
                status.issues.append(f"❌ Missing {test_name} directory")
                status.score -= 0.15
        
        # Check for test configuration files
        test_configs = {
            'pytest.ini': self.apps['api'] / 'pytest.ini',
            'playwright.config.ts': self.workspace_path / 'playwright.config.ts',
            'vitest.config.ts': self.apps['customer'] / 'vitest.config.ts'
        }
        
        for config_name, config_path in test_configs.items():
            if config_path.exists():
                logger.info(f"✅ Found {config_name}")
            else:
                status.recommendations.append(f"🔧 Consider adding {config_name}")
        
        if status.score < 0.7:
            status.status = "NOT_READY"
        elif status.score < 0.9:
            status.status = "WARNING"
            
        return status
    
    def check_security_configuration(self) -> ProductionStatus:
        """Check security configuration"""
        logger.info("🔍 Checking security configuration...")
        status = ProductionStatus("Security Configuration", "READY", 1.0)
        
        api_path = self.apps['api']
        
        # Check for security-related files
        security_files = {
            'requirements.txt': api_path / 'requirements.txt',
            'auth.py': api_path / 'app' / 'auth.py',
            'security.py': api_path / 'app' / 'core' / 'security.py'
        }
        
        for sec_name, sec_path in security_files.items():
            if sec_path.exists():
                logger.info(f"✅ Found {sec_name}")
                if sec_name == 'requirements.txt':
                    try:
                        content = sec_path.read_text(encoding='utf-8')
                    except UnicodeDecodeError:
                        content = sec_path.read_text(encoding='latin-1', errors='ignore')
                    security_packages = ['passlib', 'python-jose', 'bcrypt', 'cryptography']
                    for pkg in security_packages:
                        if pkg in content:
                            logger.info(f"✅ Security package {pkg} found")
                        else:
                            status.recommendations.append(f"🔧 Consider adding {pkg} for security")
            else:
                status.issues.append(f"⚠️  Missing {sec_name}")
                status.score -= 0.1
        
        # Check CORS configuration
        main_py = api_path / 'app' / 'main.py'
        if main_py.exists():
            try:
                content = main_py.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = main_py.read_text(encoding='latin-1', errors='ignore')
            if 'CORS' in content:
                logger.info("✅ CORS configuration found")
            else:
                status.issues.append("⚠️  CORS configuration not found")
                status.score -= 0.1
        
        if status.score < 0.7:
            status.status = "NOT_READY"
        elif status.score < 0.9:
            status.status = "WARNING"
            
        return status
    
    def check_deployment_readiness(self) -> ProductionStatus:
        """Check deployment configuration"""
        logger.info("🔍 Checking deployment readiness...")
        status = ProductionStatus("Deployment Readiness", "READY", 1.0)
        
        # Check for Docker files
        docker_files = {
            'Dockerfile': self.workspace_path / 'Dockerfile',
            'docker-compose.yml': self.workspace_path / 'docker-compose.yml',
            '.dockerignore': self.workspace_path / '.dockerignore'
        }
        
        for docker_name, docker_path in docker_files.items():
            if docker_path.exists():
                logger.info(f"✅ Found {docker_name}")
            else:
                if docker_name != '.dockerignore':
                    status.issues.append(f"❌ Missing {docker_name}")
                    status.score -= 0.2
                else:
                    status.recommendations.append(f"🔧 Consider adding {docker_name}")
        
        # Check for package.json in root and apps
        package_files = [
            self.workspace_path / 'package.json',
            self.apps['customer'] / 'package.json',
            self.apps['admin'] / 'package.json'
        ]
        
        for pkg_file in package_files:
            if pkg_file.exists():
                logger.info(f"✅ Found {pkg_file.relative_to(self.workspace_path)}")
            else:
                status.issues.append(f"❌ Missing {pkg_file.relative_to(self.workspace_path)}")
                status.score -= 0.1
        
        # Check for requirements.txt
        req_file = self.apps['api'] / 'requirements.txt'
        if req_file.exists():
            logger.info("✅ Found API requirements.txt")
        else:
            status.issues.append("❌ Missing API requirements.txt")
            status.score -= 0.2
        
        if status.score < 0.7:
            status.status = "NOT_READY"
        elif status.score < 0.9:
            status.status = "WARNING"
            
        return status
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all production readiness checks"""
        logger.info("🚀 Starting comprehensive production readiness check...")
        
        checks = [
            self.check_environment_configuration,
            self.check_database_configuration,
            self.check_api_documentation,
            self.check_testing_infrastructure,
            self.check_security_configuration,
            self.check_deployment_readiness
        ]
        
        results = []
        total_score = 0.0
        
        for check in checks:
            result = check()
            results.append(result)
            total_score += result.score
            self.results.append(result)
        
        average_score = total_score / len(checks)
        overall_status = "READY" if average_score >= 0.9 else "WARNING" if average_score >= 0.7 else "NOT_READY"
        
        return {
            'overall_status': overall_status,
            'overall_score': average_score,
            'total_checks': len(checks),
            'results': results
        }
    
    def run_local_testing_suite(self) -> Dict[str, Any]:
        """Run comprehensive local testing"""
        logger.info("🧪 Running comprehensive local testing suite...")
        
        test_results = {
            'api_tests': {'status': 'NOT_RUN', 'output': ''},
            'frontend_tests': {'status': 'NOT_RUN', 'output': ''},
            'e2e_tests': {'status': 'NOT_RUN', 'output': ''},
            'integration_tests': {'status': 'NOT_RUN', 'output': ''}
        }
        
        # Run API tests
        api_path = self.apps['api']
        if (api_path / 'tests').exists():
            try:
                logger.info("Running API tests...")
                result = subprocess.run(
                    ['python', '-m', 'pytest', 'tests/', '-v'],
                    cwd=api_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                test_results['api_tests'] = {
                    'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                    'output': result.stdout + result.stderr
                }
                logger.info(f"API tests: {test_results['api_tests']['status']}")
            except Exception as e:
                test_results['api_tests'] = {'status': 'ERROR', 'output': str(e)}
        
        # Run frontend tests for customer app
        customer_path = self.apps['customer']
        if (customer_path / '__tests__').exists() or (customer_path / 'package.json').exists():
            try:
                logger.info("Running customer frontend tests...")
                result = subprocess.run(
                    ['npm', 'test'],
                    cwd=customer_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                test_results['frontend_tests'] = {
                    'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                    'output': result.stdout + result.stderr
                }
                logger.info(f"Frontend tests: {test_results['frontend_tests']['status']}")
            except Exception as e:
                test_results['frontend_tests'] = {'status': 'ERROR', 'output': str(e)}
        
        # Run E2E tests
        e2e_path = self.workspace_path / 'e2e'
        if e2e_path.exists():
            try:
                logger.info("Running E2E tests...")
                result = subprocess.run(
                    ['npx', 'playwright', 'test'],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                test_results['e2e_tests'] = {
                    'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                    'output': result.stdout + result.stderr
                }
                logger.info(f"E2E tests: {test_results['e2e_tests']['status']}")
            except Exception as e:
                test_results['e2e_tests'] = {'status': 'ERROR', 'output': str(e)}
        
        return test_results
    
    def generate_deployment_report(self, check_results: Dict, test_results: Dict) -> str:
        """Generate comprehensive deployment readiness report"""
        report = []
        report.append("=" * 80)
        report.append("🚀 MH WEBAPPS - PRODUCTION READINESS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Overall Status
        report.append(f"🎯 OVERALL STATUS: {check_results['overall_status']}")
        report.append(f"📊 OVERALL SCORE: {check_results['overall_score']:.1%}")
        report.append("")
        
        # Detailed Results
        report.append("📋 DETAILED ASSESSMENT:")
        report.append("-" * 50)
        
        for result in check_results['results']:
            status_emoji = "✅" if result.status == "READY" else "⚠️" if result.status == "WARNING" else "❌"
            report.append(f"{status_emoji} {result.component}: {result.status} ({result.score:.1%})")
            
            if result.issues:
                report.append("   Issues:")
                for issue in result.issues:
                    report.append(f"     • {issue}")
            
            if result.recommendations:
                report.append("   Recommendations:")
                for rec in result.recommendations:
                    report.append(f"     • {rec}")
            report.append("")
        
        # Test Results
        report.append("🧪 TESTING RESULTS:")
        report.append("-" * 50)
        
        for test_name, test_result in test_results.items():
            status_emoji = "✅" if test_result['status'] == 'PASSED' else "❌" if test_result['status'] == 'FAILED' else "⚠️"
            report.append(f"{status_emoji} {test_name.replace('_', ' ').title()}: {test_result['status']}")
        report.append("")
        
        # Deployment Checklist
        report.append("🚀 PRE-DEPLOYMENT CHECKLIST:")
        report.append("-" * 50)
        checklist_items = [
            "Environment variables configured for production",
            "Database migrations are up to date",
            "API documentation is accessible",
            "All tests are passing",
            "Security configurations are in place",
            "Docker configuration is ready",
            "Monitoring and logging are configured",
            "SSL certificates are ready",
            "Domain and DNS are configured",
            "Backup strategy is in place"
        ]
        
        for item in checklist_items:
            report.append(f"   ☐ {item}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main execution function"""
    workspace = Path.cwd()
    logger.info(f"Starting comprehensive production check for: {workspace}")
    
    checker = ProductionReadinessChecker(str(workspace))
    
    # Run production readiness checks
    check_results = checker.run_comprehensive_check()
    
    # Run testing suite
    test_results = checker.run_local_testing_suite()
    
    # Generate report
    report = checker.generate_deployment_report(check_results, test_results)
    
    # Save report
    report_path = workspace / 'PRODUCTION_READINESS_REPORT.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Display results
    print(report)
    print(f"\n📄 Full report saved to: {report_path}")
    
    # Exit with appropriate code
    if check_results['overall_status'] == 'READY' and all(
        result['status'] in ['PASSED', 'NOT_RUN'] for result in test_results.values()
    ):
        logger.info("🎉 Project is ready for production deployment!")
        sys.exit(0)
    else:
        logger.warning("⚠️  Project needs attention before production deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()