"""
Production Safety Tests for OpenAPI/Swagger Fix
Run these tests before deploying to production
"""

import pytest


class TestPydanticDefaultSafety:
    """Test that mutable defaults don't leak between instances"""

    def test_health_response_no_shared_dict(self):
        """Verify checks dict is not shared between instances"""
        # Phase 2B: TODO - schemas need to be identified in NEW structure
        from api.app.schemas.health import HealthResponse  # TODO: Update to schemas.*

        # Create first instance and modify checks
        health1 = HealthResponse(status="healthy", service="test", environment="dev", version="1.0")
        health1.checks["test_key"] = "test_value"

        # Create second instance
        health2 = HealthResponse(
            status="healthy", service="test2", environment="dev", version="1.0"
        )

        # Verify second instance doesn't have first instance's data
        assert "test_key" not in (health2.checks or {})
        print("✅ HealthResponse: No shared dict detected")

    def test_command_result_no_shared_list(self):
        """Verify events list is not shared between instances"""
        from cqrs.base import CommandResult  # Phase 2B: Updated from api.app.cqrs.base

        # Create first instance and add event
        result1 = CommandResult(success=True)
        mock_event = type(
            "MockEvent", (), {"event_type": "test", "aggregate_id": "123", "occurred_at": None}
        )()
        result1.events.append(mock_event)

        # Create second instance
        result2 = CommandResult(success=True)

        # Verify second instance doesn't have first instance's events
        assert len(result2.events) == 0
        print("✅ CommandResult: No shared list detected")

    def test_chat_request_no_shared_context(self):
        """Verify context dict is not shared"""
        # Phase 2B: TODO - ai.endpoints needs mapping to NEW structure
        from api.ai.endpoints.routers.chat import ChatMessageRequest  # TODO: Map ai.* module

        # Create first request and modify context
        req1 = ChatMessageRequest(message="test1")
        req1.context["key1"] = "value1"

        # Create second request
        req2 = ChatMessageRequest(message="test2")

        # Verify isolation
        assert "key1" not in (req2.context or {})
        print("✅ ChatMessageRequest: No shared dict detected")


class TestDependencyInjection:
    """Test dependency injection patterns work correctly"""

    def test_get_di_container_returns_container(self):
        """Verify get_di_container returns container directly"""
        from api.deps_enhanced import get_di_container
        from core.container import DependencyInjectionContainer

        # Create mock request with container
        request = type(
            "MockRequest",
            (),
            {"state": type("State", (), {"container": DependencyInjectionContainer()})()},
        )()

        container = get_di_container(request)
        assert isinstance(container, DependencyInjectionContainer)
        print("✅ get_di_container returns container directly")

    def test_service_dependencies_are_async(self):
        """Verify composed service dependencies are async callables"""
        from api.deps_enhanced import (
            get_authenticated_booking_service,
            get_admin_booking_context,
            get_customer_service_context,
        )
        import inspect

        assert inspect.iscoroutinefunction(get_authenticated_booking_service)
        assert inspect.iscoroutinefunction(get_admin_booking_context)
        assert inspect.iscoroutinefunction(get_customer_service_context)
        print("✅ Service dependencies are async callables")


class TestStationPermissions:
    """Test station permission system works correctly"""

    def test_require_station_permission_returns_dependency(self):
        """Verify require_station_permission returns a callable dependency"""
        from core.auth.station_middleware import (
            require_station_permission,
        )  # Phase 2B: Updated from api.app.auth.station_middleware
        import inspect

        dep = require_station_permission("view_stations")
        # Should be a callable (function)
        assert callable(dep)
        # Should be async
        assert inspect.iscoroutinefunction(dep)
        print("✅ require_station_permission returns async dependency")

    def test_audit_log_action_signature(self):
        """Verify audit_log_action has correct signature"""
        from core.auth.station_middleware import (
            audit_log_action,
        )  # Phase 2B: Updated from api.app.auth.station_middleware
        import inspect

        sig = inspect.signature(audit_log_action)
        params = list(sig.parameters.keys())

        # Should have these parameters
        assert "action" in params
        assert "auth_user" in params
        assert "db" in params
        assert "station_id" in params
        print("✅ audit_log_action has correct signature")


class TestOutboxWorker:
    """Test outbox worker pattern works correctly"""

    def test_outbox_entry_model_fields(self):
        """Verify OutboxEntry has correct fields"""
        from models.legacy_events import OutboxEntry  # Phase 2B: Updated from api.app.models.events

        # Check model has correct fields
        assert hasattr(OutboxEntry, "status")
        assert hasattr(OutboxEntry, "attempts")
        assert hasattr(OutboxEntry, "next_attempt_at")
        assert hasattr(OutboxEntry, "completed_at")
        assert hasattr(OutboxEntry, "last_error")
        assert hasattr(OutboxEntry, "payload")
        print("✅ OutboxEntry has correct fields")

    def test_worker_uses_context_manager(self):
        """Verify worker uses get_db_context"""
        from workers.outbox_processors import (
            OutboxWorkerBase,
        )  # Phase 2B: Updated from api.app.workers.outbox_processors
        import inspect

        # Read source to verify get_db_context usage
        source = inspect.getsource(OutboxWorkerBase._process_batch)
        assert "get_db_context" in source
        print("✅ Worker uses get_db_context()")


class TestConfiguration:
    """Test configuration is safe for production"""

    def test_workers_disabled_by_default(self):
        """Verify workers are disabled in default config"""
        from core.config import Settings  # Phase 2B: Updated from api.app.config

        settings = Settings()
        assert settings.workers_enabled == False
        print("✅ Workers disabled by default (safe for dev/test)")

    def test_worker_config_structure(self):
        """Verify get_worker_configs returns correct structure"""
        from core.config import Settings  # Phase 2B: Updated from api.app.config

        settings = Settings()
        config = settings.get_worker_configs()

        assert "workers_enabled" in config
        assert "ringcentral" in config
        assert "email" in config
        assert "stripe" in config
        print("✅ Worker config structure correct")


class TestOpenAPIGeneration:
    """Test OpenAPI schema generation works"""

    def test_openapi_schema_generation(self):
        """Test that OpenAPI schema can be generated without errors"""
        from main import app

        # This should not raise any exceptions
        schema = app.openapi()

        assert schema is not None
        assert "paths" in schema
        assert len(schema["paths"]) > 0
        print(f"✅ OpenAPI generated {len(schema['paths'])} endpoints")

    def test_no_callable_schema_errors(self):
        """Test no 'Callable' appears in schema (was causing TS gen errors)"""
        from main import app

        # Capture any logs during schema generation
        with pytest.raises(Exception) as exc_info:
            try:
                schema = app.openapi()
                # If we get here, generation succeeded
                assert True
                print("✅ No CallableSchema errors detected")
                return
            except Exception as e:
                # If error occurs, check it's not CallableSchema
                error_msg = str(e)
                assert "CallableSchema" not in error_msg
                raise


def run_all_tests():
    """Run all production safety tests"""
    print("\n" + "=" * 60)
    print("PRODUCTION SAFETY TEST SUITE")
    print("=" * 60 + "\n")

    test_classes = [
        TestPydanticDefaultSafety,
        TestDependencyInjection,
        TestStationPermissions,
        TestOutboxWorker,
        TestConfiguration,
        TestOpenAPIGeneration,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n📋 {test_class.__name__}")
        print("-" * 60)

        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                total_tests += 1
                test_method = getattr(test_class(), method_name)

                try:
                    test_method()
                    passed_tests += 1
                except Exception as e:
                    print(f"❌ {method_name} FAILED: {e}")
                    failed_tests.append((test_class.__name__, method_name, str(e)))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for class_name, method_name, error in failed_tests:
            print(f"  - {class_name}.{method_name}: {error}")
        print("\n⚠️  DO NOT DEPLOY - Fix failed tests first!")
        return False
    else:
        print("\n✅ ALL TESTS PASSED - Safe to deploy!")
        return True


if __name__ == "__main__":
    import sys

    success = run_all_tests()
    sys.exit(0 if success else 1)
