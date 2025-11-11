"""
Verify Phase 2A Installation
Checks that all dependencies and modules are properly installed
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_package(package_name: str, import_name: str = None) -> bool:
    """Check if a package can be imported"""
    import_name = import_name or package_name
    try:
        __import__(import_name)
        print(f"✅ {package_name} installed")
        return True
    except ImportError as e:
        print(f"❌ {package_name} NOT installed: {e}")
        return False


def check_module(module_path: str) -> bool:
    """Check if a custom module can be imported"""
    try:
        __import__(module_path)
        print(f"✅ {module_path} module OK")
        return True
    except Exception as e:
        print(f"❌ {module_path} FAILED: {e}")
        return False


def main():
    print("=" * 60)
    print("Phase 2A Installation Verification")
    print("=" * 60)

    all_ok = True

    print("\n📦 Checking Core Dependencies:")
    all_ok &= check_package("Celery", "celery")
    all_ok &= check_package("Kombu", "kombu")
    all_ok &= check_package("Flower", "flower")
    all_ok &= check_package("Billiard", "billiard")
    all_ok &= check_package("Redis", "redis")
    all_ok &= check_package("RingCentral", "ringcentral")

    print("\n🔧 Checking Custom Modules:")
    all_ok &= check_module("workers.celery_config")
    all_ok &= check_module("workers.escalation_tasks")
    all_ok &= check_module("workers.recording_tasks")
    all_ok &= check_module("services.ringcentral_service")
    all_ok &= check_module("api.v1.webhooks.ringcentral")
    all_ok &= check_module("core.logging.pii_masking")

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ ALL CHECKS PASSED - Phase 2A is ready!")
        print("\nNext steps:")
        print("1. Run database migration: alembic upgrade head")
        print("2. Start Celery worker: celery -A workers.celery_config worker -l info")
        print("3. Start Celery beat: celery -A workers.celery_config beat -l info")
        print("4. (Optional) Start Flower: celery -A workers.celery_config flower")
    else:
        print("❌ SOME CHECKS FAILED - Please fix the issues above")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
