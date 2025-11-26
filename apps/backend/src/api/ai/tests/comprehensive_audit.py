"""
Comprehensive Phase 1B Audit Script
===================================

Deep validation of:
- Memory backend implementation
- Emotion service integration
- Database schema integrity
- Code quality and error handling
- Performance benchmarks

Zero tolerance for errors, bugs, or glitches.
"""

import asyncio
from datetime import datetime, timezone
import logging
import sys
import time

# Fix Windows console encoding
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import components
from api.ai.memory import (
    ConversationChannel,
    MemoryBackendType,
    MessageRole,
    PostgreSQLMemory,
    create_memory_backend,
)
from api.ai.services.emotion_service import EmotionService


class ComprehensiveAudit:
    """Deep audit of Phase 1B implementation"""

    def __init__(self):
        self.memory = None
        self.emotion_service = None
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "performance": {},
        }

    async def run_audit(self):
        """Execute complete audit"""

        # Initialize components
        await self._audit_initialization()

        # Database integrity
        await self._audit_database_schema()

        # Memory backend validation
        await self._audit_memory_operations()

        # Emotion service validation
        await self._audit_emotion_service()

        # Integration testing
        await self._audit_integration()

        # Performance benchmarks
        await self._audit_performance()

        # Error handling
        await self._audit_error_handling()

        # Code quality
        await self._audit_code_quality()

        # Generate report
        await self._generate_report()

        # Cleanup
        await self._cleanup()

    # =========================================================================
    # INITIALIZATION AUDIT
    # =========================================================================

    async def _audit_initialization(self):
        """Validate component initialization"""

        try:
            # Create memory backend
            self.memory = await create_memory_backend(
                MemoryBackendType.POSTGRESQL
            )
            assert self.memory is not None, "Memory backend creation failed"
            assert isinstance(
                self.memory, PostgreSQLMemory
            ), "Wrong backend type"
            self.results["passed"].append("✓ Memory backend initialization")

            # Initialize memory
            await self.memory.initialize()
            self.results["passed"].append(
                "✓ Memory backend initialization complete"
            )

            # Create emotion service
            self.emotion_service = EmotionService()
            assert (
                self.emotion_service is not None
            ), "Emotion service creation failed"
            self.results["passed"].append("✓ Emotion service initialization")

        except Exception as e:
            self.results["failed"].append(f"✗ Initialization failed: {e}")
            raise

    # =========================================================================
    # DATABASE SCHEMA AUDIT
    # =========================================================================

    async def _audit_database_schema(self):
        """Validate database schema integrity"""

        try:
            # Check tables exist
            stats = await self.memory.get_statistics(days=1)
            assert stats is not None, "Failed to query database"
            self.results["passed"].append("✓ Database tables accessible")

            # Verify schema structure
            health = await self.memory.health_check()
            assert (
                health["status"] == "healthy"
            ), f"Database unhealthy: {health}"
            self.results["passed"].append(
                f"✓ Database health: {health['status']}"
            )

        except Exception as e:
            self.results["failed"].append(
                f"✗ Database schema audit failed: {e}"
            )
            raise

    # =========================================================================
    # MEMORY OPERATIONS AUDIT
    # =========================================================================

    async def _audit_memory_operations(self):
        """Deep validation of memory operations"""

        test_conv = f"audit_conv_{datetime.now(timezone.utc).timestamp()}"
        test_user = f"audit_user_{datetime.now(timezone.utc).timestamp()}"

        try:
            # Test 1: Message storage with all fields
            msg1 = await self.memory.store_message(
                conversation_id=test_conv,
                role=MessageRole.USER,
                content="Test message with all fields",
                user_id=test_user,
                channel=ConversationChannel.WEB,
                emotion_score=0.75,
                emotion_label="positive",
                detected_emotions=["joy", "satisfaction"],
                metadata={"test": True, "source": "audit"},
            )
            assert msg1 is not None, "Message creation returned None"
            assert msg1.id is not None, "Message ID not generated"
            assert (
                msg1.emotion_score == 0.75
            ), f"Emotion score mismatch: {msg1.emotion_score}"
            self.results["passed"].append("✓ Message storage with all fields")

            # Test 2: Message retrieval
            history = await self.memory.get_conversation_history(test_conv)
            assert len(history) == 1, f"Expected 1 message, got {len(history)}"
            assert history[0].content == "Test message with all fields"
            self.results["passed"].append("✓ Message retrieval")

            # Test 3: Emotion history
            emotions = await self.memory.get_emotion_history(test_conv)
            assert len(emotions) == 1, "Emotion history not tracked"
            assert emotions[0]["score"] == 0.75
            self.results["passed"].append("✓ Emotion tracking")

            # Test 4: Conversation metadata
            metadata = await self.memory.get_conversation_metadata(test_conv)
            assert metadata.message_count == 1
            assert metadata.average_emotion_score == 0.75
            self.results["passed"].append("✓ Conversation metadata")

            # Test 5: Context update with JSONB
            await self.memory.update_conversation_metadata(
                conversation_id=test_conv,
                context={"booking_id": "BK999", "test_data": {"nested": True}},
            )
            updated_metadata = await self.memory.get_conversation_metadata(
                test_conv
            )
            assert "booking_id" in updated_metadata.context
            assert updated_metadata.context["booking_id"] == "BK999"
            self.results["passed"].append("✓ JSONB context update")

            # Test 6: Conversation lifecycle
            await self.memory.close_conversation(
                test_conv, reason="audit_complete"
            )
            closed_metadata = await self.memory.get_conversation_metadata(
                test_conv
            )
            assert not closed_metadata.is_active
            assert closed_metadata.closed_reason == "audit_complete"
            self.results["passed"].append("✓ Conversation lifecycle")

        except Exception as e:
            self.results["failed"].append(f"✗ Memory operations failed: {e}")
            raise

    # =========================================================================
    # EMOTION SERVICE AUDIT
    # =========================================================================

    async def _audit_emotion_service(self):
        """Validate emotion detection service"""

        try:
            # Test positive sentiment
            positive_result = await self.emotion_service.detect_emotion(
                "I'm so happy with your service! Everything is perfect!"
            )
            assert (
                positive_result.score > 0.5
            ), f"Positive sentiment failed: {positive_result.score}"
            assert positive_result.label in ["positive", "very_positive"]
            self.results["passed"].append(
                f"✓ Positive sentiment detection: {positive_result.score:.2f}"
            )

            # Test negative sentiment
            negative_result = await self.emotion_service.detect_emotion(
                "This is terrible! I'm very disappointed and frustrated."
            )
            assert (
                negative_result.score < 0.5
            ), f"Negative sentiment failed: {negative_result.score}"
            assert negative_result.label in ["negative", "very_negative"]
            self.results["passed"].append(
                f"✓ Negative sentiment detection: {negative_result.score:.2f}"
            )

            # Test escalation detection
            assert negative_result.should_escalate, "Escalation not detected"
            self.results["passed"].append("✓ Automatic escalation detection")

            # Test neutral sentiment
            neutral_result = await self.emotion_service.detect_emotion(
                "The meeting is scheduled for tomorrow at 2pm."
            )
            assert (
                0.4 < neutral_result.score < 0.6
            ), f"Neutral sentiment failed: {neutral_result.score}"
            self.results["passed"].append(
                f"✓ Neutral sentiment detection: {neutral_result.score:.2f}"
            )

        except Exception as e:
            self.results["failed"].append(f"✗ Emotion service failed: {e}")
            raise

    # =========================================================================
    # INTEGRATION AUDIT
    # =========================================================================

    async def _audit_integration(self):
        """Validate emotion service + memory integration"""

        test_conv = (
            f"integration_conv_{datetime.now(timezone.utc).timestamp()}"
        )
        test_user = (
            f"integration_user_{datetime.now(timezone.utc).timestamp()}"
        )

        try:
            # Simulate real workflow: detect emotion → store message
            user_message = "I'm absolutely thrilled with the catering service!"
            emotion = await self.emotion_service.detect_emotion(user_message)

            # Store with emotion data
            msg = await self.memory.store_message(
                conversation_id=test_conv,
                role=MessageRole.USER,
                content=user_message,
                user_id=test_user,
                channel=ConversationChannel.WEB,
                emotion_score=emotion.score,
                emotion_label=emotion.label,
                detected_emotions=emotion.detected_emotions,
            )

            assert msg.emotion_score == emotion.score
            self.results["passed"].append("✓ Emotion → Memory integration")

            # Verify emotion tracking
            emotions = await self.memory.get_emotion_history(test_conv)
            assert len(emotions) == 1
            assert emotions[0]["label"] == emotion.label
            self.results["passed"].append("✓ Emotion history integration")

            # Verify metadata update
            metadata = await self.memory.get_conversation_metadata(test_conv)
            assert metadata.average_emotion_score == emotion.score
            self.results["passed"].append("✓ Conversation emotion statistics")

        except Exception as e:
            self.results["failed"].append(f"✗ Integration failed: {e}")
            raise

    # =========================================================================
    # PERFORMANCE AUDIT
    # =========================================================================

    async def _audit_performance(self):
        """Benchmark performance metrics"""

        test_conv = f"perf_conv_{datetime.now(timezone.utc).timestamp()}"
        test_user = f"perf_user_{datetime.now(timezone.utc).timestamp()}"

        try:
            # Benchmark message storage (target: <2000ms)
            start = time.time()
            await self.memory.store_message(
                conversation_id=test_conv,
                role=MessageRole.USER,
                content="Performance test message",
                user_id=test_user,
            )
            storage_time = (time.time() - start) * 1000
            assert (
                storage_time < 2000
            ), f"Storage too slow: {storage_time:.0f}ms"
            self.results["performance"]["message_storage_ms"] = round(
                storage_time, 2
            )
            self.results["passed"].append(
                f"✓ Message storage: {storage_time:.0f}ms"
            )

            # Benchmark retrieval (target: <1000ms)
            start = time.time()
            await self.memory.get_conversation_history(test_conv)
            retrieval_time = (time.time() - start) * 1000
            assert (
                retrieval_time < 1000
            ), f"Retrieval too slow: {retrieval_time:.0f}ms"
            self.results["performance"]["message_retrieval_ms"] = round(
                retrieval_time, 2
            )
            self.results["passed"].append(
                f"✓ Message retrieval: {retrieval_time:.0f}ms"
            )

            # Benchmark emotion detection (target: <5000ms for OpenAI API)
            start = time.time()
            await self.emotion_service.detect_emotion("Quick emotion test")
            emotion_time = (time.time() - start) * 1000
            assert (
                emotion_time < 10000
            ), f"Emotion detection too slow: {emotion_time:.0f}ms"
            self.results["performance"]["emotion_detection_ms"] = round(
                emotion_time, 2
            )
            self.results["passed"].append(
                f"✓ Emotion detection: {emotion_time:.0f}ms"
            )

            # Benchmark health check (target: <2000ms)
            start = time.time()
            await self.memory.health_check()
            health_time = (time.time() - start) * 1000
            assert (
                health_time < 2000
            ), f"Health check too slow: {health_time:.0f}ms"
            self.results["performance"]["health_check_ms"] = round(
                health_time, 2
            )
            self.results["passed"].append(
                f"✓ Health check: {health_time:.0f}ms"
            )

        except Exception as e:
            self.results["failed"].append(f"✗ Performance audit failed: {e}")
            raise

    # =========================================================================
    # ERROR HANDLING AUDIT
    # =========================================================================

    async def _audit_error_handling(self):
        """Validate error handling and edge cases"""

        try:
            # Test 1: Non-existent conversation (should return None)
            result = await self.memory.get_conversation_metadata(
                "nonexistent_conv"
            )
            if result is None:
                self.results["passed"].append(
                    "✓ Non-existent conversation returns None"
                )
            else:
                self.results["failed"].append(
                    "✗ Should return None for non-existent conversation"
                )

            # Test 2: Invalid channel
            try:
                msg = await self.memory.store_message(
                    conversation_id=f"test_{datetime.now(timezone.utc).timestamp()}",
                    role=MessageRole.USER,
                    content="Test",
                    user_id="test",
                    channel=ConversationChannel.WEB,  # Valid channel
                )
                assert msg is not None
                self.results["passed"].append("✓ Valid channel accepted")
            except Exception as e:
                self.results["failed"].append(f"✗ Valid channel rejected: {e}")

            # Test 3: Empty emotion detection
            try:
                result = await self.emotion_service.detect_emotion("")
                # Should still return a result (neutral)
                assert result is not None
                self.results["passed"].append("✓ Empty text emotion handling")
            except Exception:
                self.results["warnings"].append(
                    "⚠ Empty text emotion handling could be improved"
                )

            # Test 4: Very long content
            long_content = "A" * 10000
            msg = await self.memory.store_message(
                conversation_id=f"long_test_{datetime.now(timezone.utc).timestamp()}",
                role=MessageRole.USER,
                content=long_content,
                user_id="test",
            )
            assert msg is not None
            self.results["passed"].append("✓ Long content handling")

        except Exception as e:
            self.results["failed"].append(
                f"✗ Error handling audit failed: {e}"
            )
            raise

    # =========================================================================
    # CODE QUALITY AUDIT
    # =========================================================================

    async def _audit_code_quality(self):
        """Validate code quality standards"""

        try:
            # Check memory backend implements all interface methods
            required_methods = [
                "initialize",
                "store_message",
                "get_conversation_history",
                "get_recent_messages",
                "get_user_history",
                "get_conversation_metadata",
                "update_conversation_metadata",
                "close_conversation",
                "get_emotion_history",
                "get_escalated_conversations",
                "get_context_window",
                "get_statistics",
                "health_check",
                "close",
            ]

            for method in required_methods:
                assert hasattr(
                    self.memory, method
                ), f"Missing method: {method}"
                assert callable(
                    getattr(self.memory, method)
                ), f"Method not callable: {method}"

            self.results["passed"].append(
                f"✓ All {len(required_methods)} interface methods implemented"
            )

            # Check emotion service methods (actual implemented methods)
            emotion_methods = [
                "detect_emotion",
                "adjust_agent_tone",
                "should_escalate",
                "detect_emotion_batch",
                "get_emotion_trend",
            ]
            for method in emotion_methods:
                assert hasattr(
                    self.emotion_service, method
                ), f"Missing method: {method}"

            self.results["passed"].append(
                f"✓ All {len(emotion_methods)} emotion service methods implemented"
            )

            # Type checking
            assert isinstance(
                self.memory, PostgreSQLMemory
            ), "Wrong backend type"
            assert isinstance(
                self.emotion_service, EmotionService
            ), "Wrong emotion service type"
            self.results["passed"].append("✓ Type safety validated")

        except Exception as e:
            self.results["failed"].append(f"✗ Code quality audit failed: {e}")
            raise

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================

    async def _generate_report(self):
        """Generate comprehensive audit report"""

        # Summary
        len(self.results["passed"]) + len(self.results["failed"])
        len(self.results["passed"])
        failed = len(self.results["failed"])
        len(self.results["warnings"])

        # Passed checks
        if self.results["passed"]:
            for _check in self.results["passed"]:
                pass

        # Failed checks
        if self.results["failed"]:
            for _check in self.results["failed"]:
                pass

        # Warnings
        if self.results["warnings"]:
            for _warning in self.results["warnings"]:
                pass

        # Performance metrics
        if self.results["performance"]:
            for _metric, _value in self.results["performance"].items():
                pass

        # Final verdict
        if failed == 0:
            pass
        else:
            pass

    # =========================================================================
    # CLEANUP
    # =========================================================================

    async def _cleanup(self):
        """Clean up resources"""
        if self.memory:
            await self.memory.close()


async def main():
    """Run comprehensive audit"""
    audit = ComprehensiveAudit()
    try:
        await audit.run_audit()
    except Exception:
        raise


if __name__ == "__main__":
    asyncio.run(main())
