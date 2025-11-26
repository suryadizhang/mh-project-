"""
Integration Tests for Follow-Up Scheduler with AI Orchestrator
================================================================

Tests the complete integration including:
- Orchestrator initialization with scheduler
- Booking confirmation triggering follow-ups
- Inactive user detection and re-engagement
- End-to-end follow-up execution
- Message sending via orchestrator callback
"""

import asyncio
from datetime import datetime, timezone, timedelta
import logging
import os
import sys
import unittest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment
os.environ["MEMORY_BACKEND"] = "postgresql"
os.environ["SCHEDULER_TIMEZONE"] = "UTC"


class TestSchedulerIntegration(unittest.TestCase):
    """Integration tests for scheduler with orchestrator"""

    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
        logger.info("=" * 80)
        logger.info("INTEGRATION TEST SUITE: Follow-Up Scheduler with AI Orchestrator")
        logger.info("=" * 80)

    def setUp(self):
        """Set up each test"""
        self.loop.run_until_complete(self._setup())

    async def _setup(self):
        """Async setup"""
        from api.ai.memory import get_memory_backend
        from api.ai.memory.memory_backend import MessageRole
        from api.ai.orchestrator import AIOrchestrator

        # Initialize orchestrator (which initializes scheduler)
        self.orchestrator = AIOrchestrator(use_router=False)
        await self.orchestrator.start()

        # Get references
        self.scheduler = self.orchestrator.scheduler
        self.memory = get_memory_backend()
        self.MessageRole = MessageRole

        # Test IDs
        import time

        self.test_user_id = f"integration_test_user_{time.time()}"
        self.test_conv_id = f"integration_test_conv_{time.time()}"

    def tearDown(self):
        """Tear down each test"""
        self.loop.run_until_complete(self._cleanup())

    async def _cleanup(self):
        """Async cleanup"""
        # Stop orchestrator
        if hasattr(self, "orchestrator"):
            await self.orchestrator.stop()

        # Clean up test data
        await self._cleanup_test_data()

    async def _cleanup_test_data(self):
        """Clean up test data from database"""
        from core.database import get_db_context
        from sqlalchemy import text

        try:
            async with get_db_context() as db:
                # Delete test follow-ups
                await db.execute(
                    text("DELETE FROM scheduled_followups WHERE user_id LIKE :pattern"),
                    {"pattern": f"{self.test_user_id}%"},
                )
                # Delete test messages
                await db.execute(
                    text("DELETE FROM ai_messages WHERE conversation_id LIKE :pattern"),
                    {"pattern": f"{self.test_conv_id}%"},
                )
                # Delete test conversations
                await db.execute(
                    text("DELETE FROM ai_conversations WHERE id LIKE :pattern"),
                    {"pattern": f"{self.test_conv_id}%"},
                )
                await db.commit()
        except Exception as e:
            logger.exception(f"Cleanup error: {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test class"""
        cls.loop.close()
        logger.info("=" * 80)
        logger.info("INTEGRATION TEST SUITE COMPLETE")
        logger.info("=" * 80)

    # =========================================================================
    # TEST 1: Orchestrator Initialization
    # =========================================================================

    def test_01_orchestrator_initialization(self):
        """Test 1: Orchestrator initializes with scheduler"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Orchestrator Initialization with Scheduler")
        logger.info("=" * 80)

        async def run_test():
            # Check orchestrator has scheduler
            self.assertIsNotNone(self.orchestrator.scheduler, "Orchestrator should have scheduler")

            # Check scheduler is running
            health = await self.scheduler.health_check()
            self.assertEqual(health["status"], "healthy")
            self.assertTrue(health["scheduler_running"])

            logger.info("✅ PASSED: Orchestrator initialized with scheduler")

        self.loop.run_until_complete(run_test())
        logger.info("ok")

    # =========================================================================
    # TEST 2: Booking Confirmation Triggers Follow-Up
    # =========================================================================

    def test_02_booking_confirmation_followup(self):
        """Test 2: Booking confirmation triggers post-event follow-up"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Booking Confirmation Triggers Follow-Up")
        logger.info("=" * 80)

        async def run_test():
            # Create a conversation with positive emotion
            conv_id = f"{self.test_conv_id}_booking"
            user_id = f"{self.test_user_id}_booking"

            # Store a message with high emotion
            await self.memory.store_message(
                conversation_id=conv_id,
                role=self.MessageRole.USER,
                content="I'm so excited about my upcoming event!",
                user_id=user_id,
                emotion_score=0.9,
                emotion_label="positive",
            )

            # Simulate booking confirmation
            event_date = datetime.now(timezone.utc) + timedelta(days=7)
            job_id = await self.orchestrator.schedule_post_event_followup(
                conversation_id=conv_id,
                user_id=user_id,
                event_date=event_date,
                booking_id="TEST_BOOKING_123",
            )

            self.assertIsNotNone(job_id, "Should return job ID")
            logger.info(f"Scheduled follow-up: {job_id}")

            # Verify job was created in database
            jobs = await self.scheduler.get_scheduled_followups(user_id=user_id)
            self.assertEqual(len(jobs), 1, "Should have 1 follow-up scheduled")

            job = jobs[0]
            self.assertEqual(job.trigger_type, "post_event")
            self.assertEqual(job.status, "pending")
            self.assertIn("post_event", job.template_id)

            logger.info(
                f"✅ PASSED: Booking confirmation triggered follow-up (template: {job.template_id})"
            )

        self.loop.run_until_complete(run_test())
        logger.info("ok")

    # =========================================================================
    # TEST 3: Emotion-Based Template Selection
    # =========================================================================

    def test_03_emotion_based_template_selection(self):
        """Test 3: Follow-ups use emotion-appropriate templates"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: Emotion-Based Template Selection")
        logger.info("=" * 80)

        async def run_test():
            # Test high emotion
            conv_high = f"{self.test_conv_id}_emotion_high"
            user_high = f"{self.test_user_id}_emotion_high"

            await self.memory.store_message(
                conversation_id=conv_high,
                role=self.MessageRole.USER,
                content="Absolutely amazing service!",
                user_id=user_high,
                emotion_score=0.95,
                emotion_label="positive",
            )

            event_date = datetime.now(timezone.utc) + timedelta(days=3)
            await self.orchestrator.schedule_post_event_followup(
                conversation_id=conv_high, user_id=user_high, event_date=event_date
            )

            # Test low emotion
            conv_low = f"{self.test_conv_id}_emotion_low"
            user_low = f"{self.test_user_id}_emotion_low"

            await self.memory.store_message(
                conversation_id=conv_low,
                role=self.MessageRole.USER,
                content="I have some concerns about the service",
                user_id=user_low,
                emotion_score=0.2,
                emotion_label="negative",
            )

            await self.orchestrator.schedule_post_event_followup(
                conversation_id=conv_low, user_id=user_low, event_date=event_date
            )

            # Verify templates
            jobs_high = await self.scheduler.get_scheduled_followups(user_id=user_high)
            jobs_low = await self.scheduler.get_scheduled_followups(user_id=user_low)

            self.assertEqual(len(jobs_high), 1)
            self.assertEqual(len(jobs_low), 1)

            self.assertEqual(jobs_high[0].template_id, "post_event_high_emotion")
            self.assertEqual(jobs_low[0].template_id, "post_event_low_emotion")

            logger.info(f"✅ PASSED: High emotion → {jobs_high[0].template_id}")
            logger.info(f"✅ PASSED: Low emotion → {jobs_low[0].template_id}")

        self.loop.run_until_complete(run_test())
        logger.info("ok")

    # =========================================================================
    # TEST 4: Inactive User Detection
    # =========================================================================

    def test_04_inactive_user_detection(self):
        """Test 4: Inactive users are detected and re-engaged"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: Inactive User Detection and Re-Engagement")
        logger.info("=" * 80)

        async def run_test():
            from api.ai.scheduler.inactive_user_detection import (
                detect_inactive_users,
                schedule_reengagement_campaigns,
            )

            # Create an inactive user (31 days ago)
            conv_id = f"{self.test_conv_id}_inactive"
            user_id = f"{self.test_user_id}_inactive"

            # Create conversation with old last_message_at
            from db.models.ai import UnifiedConversation
            from core.database import get_db_context

            inactive_date = datetime.now(timezone.utc) - timedelta(days=31)

            async with get_db_context() as db:
                conversation = UnifiedConversation(
                    id=conv_id,
                    user_id=user_id,
                    channel="web",
                    started_at=inactive_date,
                    last_message_at=inactive_date,
                    message_count=1,
                    context={},
                    is_active=True,
                )
                db.add(conversation)
                await db.commit()

            # Detect inactive users
            inactive_users = await detect_inactive_users(inactive_threshold_days=30, limit=100)

            # Find our test user
            test_user = next((u for u in inactive_users if u["user_id"] == user_id), None)
            self.assertIsNotNone(test_user, f"Should detect inactive user {user_id}")
            logger.info(f"Detected inactive user: {user_id}")

            # Schedule re-engagement
            scheduled_count = await schedule_reengagement_campaigns(
                scheduler=self.scheduler, inactive_threshold_days=30, batch_size=100
            )

            self.assertGreater(scheduled_count, 0, "Should schedule at least one re-engagement")

            # Verify re-engagement job was created
            jobs = await self.scheduler.get_scheduled_followups(user_id=user_id)
            reengagement_jobs = [j for j in jobs if j.trigger_type == "reengagement"]

            self.assertGreater(len(reengagement_jobs), 0, "Should have re-engagement job")
            logger.info(f"✅ PASSED: Scheduled {len(reengagement_jobs)} re-engagement(s)")

        self.loop.run_until_complete(run_test())
        logger.info("ok")

    # =========================================================================
    # TEST 5: Message Callback Integration
    # =========================================================================

    def test_05_message_callback_integration(self):
        """Test 5: Follow-up execution sends messages via orchestrator"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 5: Message Callback Integration")
        logger.info("=" * 80)

        async def run_test():
            # Create a test conversation
            conv_id = f"{self.test_conv_id}_callback"
            user_id = f"{self.test_user_id}_callback"

            await self.memory.store_message(
                conversation_id=conv_id,
                role=self.MessageRole.USER,
                content="Test message",
                user_id=user_id,
                emotion_score=0.7,
                emotion_label="neutral",
            )

            # Schedule a follow-up that executes immediately
            from api.ai.scheduler.follow_up_scheduler import (
                FollowUpStatus,
                CustomerEngagementFollowUp,
            )
            from core.database import get_db_context

            job_id = f"callback_test_{user_id}"
            followup = CustomerEngagementFollowUp(
                id=job_id,
                conversation_id=conv_id,
                user_id=user_id,
                trigger_type="post_event",
                trigger_data={"test": True},
                scheduled_at=datetime.now(timezone.utc),  # Execute now
                status=FollowUpStatus.PENDING.value,
                template_id="post_event_neutral_emotion",
                message_content="Test follow-up message",
                created_at=datetime.now(timezone.utc),
                retry_count=0,
            )

            async with get_db_context() as db:
                db.add(followup)
                await db.commit()

            # Execute the follow-up manually
            await self.scheduler._execute_followup(job_id)

            # Verify status changed to EXECUTED
            async with get_db_context() as db:
                from sqlalchemy import select

                stmt = select(CustomerEngagementFollowUp).where(CustomerEngagementFollowUp.id == job_id)
                result = await db.execute(stmt)
                updated_followup = result.scalar_one_or_none()

                self.assertIsNotNone(updated_followup)
                self.assertEqual(updated_followup.status, FollowUpStatus.EXECUTED.value)
                self.assertIsNotNone(updated_followup.executed_at)

            logger.info("✅ PASSED: Follow-up executed and marked as completed")

        self.loop.run_until_complete(run_test())
        logger.info("ok")


def run_integration_tests():
    """Run all integration tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSchedulerIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary

    if result.wasSuccessful():
        pass
    else:
        pass

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_integration_tests())

