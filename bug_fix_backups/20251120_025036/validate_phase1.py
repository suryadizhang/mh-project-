#!/usr/bin/env python3
"""
Phase 1 Validation Script
Tests the implemented architectural patterns: DI, Repository Pattern, Error Handling
"""
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_dependency_injection():
    """Test dependency injection container functionality"""

    try:
        from core.container import DependencyInjectionContainer

        # Test basic container functionality
        container = DependencyInjectionContainer()

        # Test value registration
        container.register_value("test_config", {"key": "value"})
        config = container.resolve("test_config")
        assert config["key"] == "value", "Value registration failed"

        # Test singleton registration
        class TestService:
            def __init__(self):
                self.created_at = "singleton"

        container.register_singleton("test_service", TestService)
        service1 = container.resolve("test_service")
        service2 = container.resolve("test_service")
        assert service1 is service2, "Singleton registration failed"

        # Test transient registration
        class TransientService:
            def __init__(self):
                self.created_at = "transient"

        container.register_transient("transient_service", TransientService)
        transient1 = container.resolve("transient_service")
        transient2 = container.resolve("transient_service")
        assert transient1 is not transient2, "Transient registration failed"

        return True

    except Exception:
        return False


def test_repository_pattern():
    """Test repository pattern implementation"""

    try:
        from core.repository import (
            FilterCriteria,
            SortCriteria,
        )
        from models.booking import BookingStatus
        from models.customer import CustomerStatus

        # Test filter criteria
        filter_criteria = FilterCriteria(
            field="status", operator="eq", value=BookingStatus.CONFIRMED
        )
        assert filter_criteria.field == "status", "FilterCriteria failed"

        # Test sort criteria
        sort_criteria = SortCriteria(field="created_at", direction="desc")
        assert sort_criteria.field == "created_at", "SortCriteria failed"

        # Test model enums
        assert BookingStatus.PENDING == "pending", "BookingStatus enum failed"
        assert CustomerStatus.ACTIVE == "active", "CustomerStatus enum failed"

        return True

    except Exception:
        return False


def test_error_handling():
    """Test centralized error handling"""

    try:
        from core.exceptions import (
            ErrorCode,
            NotFoundException,
            create_error_response,
            create_success_response,
            raise_not_found,
        )

        # Test error codes
        assert ErrorCode.NOT_FOUND == "NOT_FOUND", "ErrorCode enum failed"

        # Test exception creation
        try:
            raise_not_found("Customer", "123")
        except NotFoundException as e:
            assert "Customer" in str(e), "NotFoundException failed"
            assert e.status_code == 404, "Status code incorrect"

        # Test success response
        success_response = create_success_response(
            data={"test": "data"}, message="Test successful"
        )
        assert success_response["success"], "Success response failed"

        # Test error response
        error_response = create_error_response(
            message="Test error", error_code=ErrorCode.VALIDATION_ERROR
        )
        assert not error_response["success"], "Error response failed"

        return True

    except Exception:
        return False


def test_service_registry():
    """Test service registry integration"""

    try:
        # Test direct ServiceRegistry class functionality
        from core.container import DependencyInjectionContainer

        # Create a simple test registry
        container = DependencyInjectionContainer()

        # Test basic registry-like functionality
        test_config = {"database_url": "sqlite:///test.db", "debug": True}

        # Register individual config values
        for key, value in test_config.items():
            container.register_value(f"config_{key}", value)

        # Register full config
        container.register_value("app_config", test_config)

        # Test resolution
        db_url = container.resolve("config_database_url")
        assert db_url == "sqlite:///test.db", "Config registration failed"

        full_config = container.resolve("app_config")
        assert full_config["debug"], "Full config registration failed"

        return True

    except Exception:
        return False


def test_models():
    """Test model definitions"""

    try:
        from models.booking import Booking, BookingStatus
        from models.customer import (
            Customer,
            CustomerPreference,
            CustomerStatus,
        )

        # Test booking status methods
        assert hasattr(
            Booking, "is_active"
        ), "Booking missing is_active property"
        assert hasattr(
            Booking, "can_be_cancelled"
        ), "Booking missing can_be_cancelled property"

        # Test customer methods
        assert hasattr(
            Customer, "full_name"
        ), "Customer missing full_name property"
        assert hasattr(Customer, "is_vip"), "Customer missing is_vip property"

        # Test enums
        assert len(list(BookingStatus)) >= 5, "BookingStatus enum incomplete"
        assert len(list(CustomerStatus)) >= 3, "CustomerStatus enum incomplete"
        assert (
            len(list(CustomerPreference)) >= 3
        ), "CustomerPreference enum incomplete"

        return True

    except Exception:
        return False


def main():
    """Run all validation tests"""

    tests = [
        test_dependency_injection,
        test_repository_pattern,
        test_error_handling,
        test_service_registry,
        test_models,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
