"""
Comprehensive Error Check Script for MyHibachi AI System
Validates all components, imports, configurations, and potential issues
"""

import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


def check_python_environment():
    """Check Python environment and version"""
    print(f"🐍 Python Version: {sys.version}")
    print(f"📍 Python Executable: {sys.executable}")
    print(f"📂 Current Working Directory: {os.getcwd()}")
    return True


def check_dependencies():
    """Check all required dependencies"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "structlog",
        "psutil",
        "prometheus_client",
        "requests",
        "websockets",
        "openai",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError as e:
            missing_packages.append(package)
            print(f"❌ {package}: {e}")

    return len(missing_packages) == 0, missing_packages


def check_project_structure():
    """Check project directory structure"""
    base_path = Path("c:/Users/surya/projects/MH webapps")

    required_dirs = [
        "myhibachi-ai-backend",
        "myhibachi-ai-backend/app",
        "myhibachi-ai-backend/logs",
        "myhibachi-frontend",
        "myhibachi-frontend/src/components/chat",
    ]

    required_files = [
        "myhibachi-ai-backend/app/main.py",
        "myhibachi-ai-backend/app/logging_config.py",
        "myhibachi-ai-backend/app/monitoring.py",
        "myhibachi-ai-backend/test_backend.py",
        "myhibachi-ai-backend/verify_system.py",
        "myhibachi-frontend/src/components/chat/ChatWidget.tsx",
    ]

    print("\n📁 Checking Directory Structure:")
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            missing_dirs.append(dir_path)
            print(f"❌ {dir_path}")

    print("\n📄 Checking Required Files:")
    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")

    return (
        len(missing_dirs) == 0 and len(missing_files) == 0,
        missing_dirs,
        missing_files,
    )


def check_module_imports():
    """Check if our custom modules can be imported"""
    modules_to_test = [
        ("app.logging_config", "setup_logging"),
        ("app.monitoring", "PerformanceMonitor"),
        ("test_backend", None),
        ("verify_system", "SystemVerification"),
    ]

    print("\n🔧 Checking Module Imports:")
    failed_imports = []

    # Change to backend directory for imports
    original_cwd = os.getcwd()
    backend_dir = Path(
        "c:/Users/surya/projects/MH webapps/myhibachi-ai-backend"
    )

    try:
        os.chdir(backend_dir)
        sys.path.insert(0, str(backend_dir))

        for module_name, attribute in modules_to_test:
            try:
                module = __import__(
                    module_name, fromlist=[attribute] if attribute else []
                )
                if attribute:
                    getattr(module, attribute)
                    print(f"✅ {module_name}.{attribute}")
                else:
                    print(f"✅ {module_name}")
            except Exception as e:
                failed_imports.append((module_name, str(e)))
                print(f"❌ {module_name}: {e}")

    finally:
        os.chdir(original_cwd)
        if str(backend_dir) in sys.path:
            sys.path.remove(str(backend_dir))

    return len(failed_imports) == 0, failed_imports


def check_configuration_files():
    """Check configuration files for errors"""
    config_files = [
        "myhibachi-ai-backend/.env",
        "myhibachi-ai-backend/.env.example",
        "myhibachi-frontend/next.config.mjs",
        "myhibachi-frontend/package.json",
    ]

    print("\n⚙️ Checking Configuration Files:")
    config_issues = []
    base_path = Path("c:/Users/surya/projects/MH webapps")

    for config_file in config_files:
        file_path = base_path / config_file
        try:
            if file_path.exists():
                if file_path.suffix == ".json":
                    with open(file_path) as f:
                        json.load(f)  # Validate JSON
                print(f"✅ {config_file}")
            else:
                config_issues.append(f"{config_file} not found")
                print(f"⚠️ {config_file} not found")
        except Exception as e:
            config_issues.append(f"{config_file}: {e}")
            print(f"❌ {config_file}: {e}")

    return len(config_issues) == 0, config_issues


def check_database_files():
    """Check database-related files"""
    db_files = [
        "myhibachi-ai-backend/alembic.ini",
        "myhibachi-ai-backend/ai_chat.db",
    ]

    print("\n🗄️ Checking Database Files:")
    db_issues = []
    base_path = Path("c:/Users/surya/projects/MH webapps")

    for db_file in db_files:
        file_path = base_path / db_file
        if file_path.exists():
            print(f"✅ {db_file}")
        else:
            db_issues.append(f"{db_file} not found")
            print(f"⚠️ {db_file} not found (may be created on first run)")

    return True, db_issues  # Don't fail for missing DB files


def check_port_availability():
    """Check if required ports are available"""
    import socket

    ports_to_check = [8001, 8002, 3000, 8000]
    print("\n🔌 Checking Port Availability:")

    port_issues = []
    for port in ports_to_check:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                print(f"✅ Port {port} available")
            except OSError:
                port_issues.append(f"Port {port} in use")
                print(f"⚠️ Port {port} in use (may be our services)")

    return True, port_issues  # Don't fail for ports in use


def check_environment_variables():
    """Check important environment variables"""
    print("\n🌍 Checking Environment Variables:")

    # Check if we can access the .env file
    env_path = Path(
        "c:/Users/surya/projects/MH webapps/myhibachi-ai-backend/.env"
    )

    if env_path.exists():
        print("✅ .env file exists")
        try:
            with open(env_path) as f:
                content = f.read()
                if "OPENAI_API_KEY" in content:
                    print("✅ OPENAI_API_KEY configured")
                else:
                    print("⚠️ OPENAI_API_KEY not found in .env")
        except Exception as e:
            print(f"❌ Error reading .env: {e}")
    else:
        print("⚠️ .env file not found")

    return True, []


def generate_error_report():
    """Generate comprehensive error report"""
    print("=" * 80)
    print("🔍 COMPREHENSIVE ERROR CHECK - MyHibachi AI System")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    all_checks_passed = True
    issues_found = []

    # Run all checks
    checks = [
        ("Python Environment", check_python_environment),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Module Imports", check_module_imports),
        ("Configuration Files", check_configuration_files),
        ("Database Files", check_database_files),
        ("Port Availability", check_port_availability),
        ("Environment Variables", check_environment_variables),
    ]

    for check_name, check_function in checks:
        print(f"\n🧪 {check_name}:")
        try:
            result = check_function()
            if isinstance(result, tuple):
                passed, issues = result[0], result[1:]
                if not passed:
                    all_checks_passed = False
                    issues_found.extend(issues[0] if issues else [])
            else:
                if not result:
                    all_checks_passed = False
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            all_checks_passed = False
            issues_found.append(f"{check_name}: {e}")

    # Summary
    print("\n" + "=" * 80)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - No critical errors found!")
        print("🚀 System ready for deployment and testing")
    else:
        print("⚠️ ISSUES FOUND - Review the following:")
        for issue in issues_found:
            if isinstance(issue, (list, tuple)):
                for sub_issue in issue:
                    print(f"  • {sub_issue}")
            else:
                print(f"  • {issue}")

    print("=" * 80)
    return all_checks_passed, issues_found


if __name__ == "__main__":
    try:
        success, issues = generate_error_report()

        # Save report to file
        report_path = Path(
            "c:/Users/surya/projects/MH webapps/error_check_report.json"
        )
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "issues": issues,
            "python_version": sys.version,
            "python_executable": sys.executable,
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"📄 Full report saved to: {report_path}")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Error check script failed: {e}")
        traceback.print_exc()
        sys.exit(1)
