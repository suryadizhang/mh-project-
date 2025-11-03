"""
Test Suite for Smart Follow-Up Scheduler
========================================

Comprehensive tests for the follow-up scheduling system covering:
- Post-event follow-up scheduling
- Re-engagement campaign scheduling
- Follow-up cancellation
- Scheduled follow-ups retrieval
- Follow-up execution
- Emotion-based template selection
- Duplicate prevention
- Timezone handling
- Database persistence
- Health checks

Run with:
    cd apps/backend
    export PYTHONPATH=$PWD/src
    python src/api/ai/tests/test_follow_up_scheduler.py
"""

import unittest
import asyncio
from datetime import datetime, timedelta
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env.example')
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from api.ai.scheduler import (
    FollowUpScheduler,
    FollowUpTriggerType,
    FollowUpStatus,
    FOLLOW_UP_TEMPLATES
)
from api.ai.memory.memory_factory import get_memory_backend
from api.ai.memory.memory_backend import MessageRole, ConversationChannel
from api.ai.services.emotion_service import EmotionService
from core.database import get_db_context
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFollowUpScheduler(unittest.TestCase):
    """Test suite for FollowUpScheduler"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        logger.info("Setting up Follow-Up Scheduler test environment...")
        
        # Set test environment
        os.environ['MEMORY_BACKEND'] = 'postgresql'
        os.environ['OPENAI_API_KEY'] = 'test-key'  # Mock key for testing
        
        cls.test_user_id = f"test_user_{datetime.now().timestamp()}"
        cls.test_conv_id = f"test_conv_{datetime.now().timestamp()}"
        
        # Create single event loop for all tests
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        try:
            if cls.loop and not cls.loop.is_closed():
                cls.loop.close()
        except Exception as e:
            logger.error(f"Error closing event loop: {e}")
    
    def setUp(self):
        """Set up test fixtures"""
        self.memory = self.loop.run_until_complete(get_memory_backend())
        self.emotion_service = EmotionService()
        self.scheduler = FollowUpScheduler(self.memory, self.emotion_service)
        
        # Start scheduler
        self.loop.run_until_complete(self.scheduler.start())
    
    def tearDown(self):
        """Clean up after each test"""
        try:
            # Stop scheduler gracefully
            if self.scheduler and self.scheduler._running:
                if self.scheduler.scheduler and self.scheduler.scheduler.running:
                    self.scheduler.scheduler.shutdown(wait=False)
                self.scheduler._running = False
        except Exception as e:
            logger.warning(f"Error stopping scheduler: {e}")
        
        # Clean up test data
        try:
            self.loop.run_until_complete(self._cleanup_test_data())
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    async def _cleanup_test_data(self):
        """Clean up test follow-ups from database"""
        try:
            async with get_db_context() as db:
                # Delete test follow-ups
                await db.execute(text("""
                    DELETE FROM scheduled_followups 
                    WHERE user_id LIKE :pattern
                """), {"pattern": f"{self.test_user_id}%"})
                
                # Delete test conversations
                await db.execute(text("""
                    DELETE FROM ai_messages 
                    WHERE conversation_id LIKE :pattern
                """), {"pattern": f"{self.test_conv_id}%"})
                
                await db.execute(text("""
                    DELETE FROM ai_conversations 
                    WHERE id LIKE :pattern
                """), {"pattern": f"{self.test_conv_id}%"})
                
                await db.commit()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def test_01_scheduler_initialization(self):
        """Test 1: Scheduler Initialization"""
        logger.info("\nTEST 1: Scheduler Initialization")
        
        result = self.loop.run_until_complete(self.scheduler.health_check())
        
        assert result["status"] == "healthy", "Scheduler should be healthy"
        assert result["scheduler_running"] is True, "Scheduler should be running"
        logger.info("✓ PASSED: Scheduler initialized successfully")
    
    def test_02_schedule_post_event_followup(self):
        """Test 2: Schedule Post-Event Follow-Up"""
        logger.info("\nTEST 2: Schedule Post-Event Follow-Up")
        
        async def run_test():
            # Create test conversation with high emotion
            await self.memory.store_message(
                conversation_id=self.test_conv_id,
                role=MessageRole.USER,
                content="I'm so excited about the event!",
                user_id=self.test_user_id,
                emotion_score=0.9,
                emotion_label="positive"
            )
            
            # Schedule follow-up for 2 days from now
            event_date = datetime.utcnow() + timedelta(days=2)
            job_id = await self.scheduler.schedule_post_event_followup(
                conversation_id=self.test_conv_id,
                user_id=self.test_user_id,
                event_date=event_date,
                booking_id="BK123",
                followup_delay=timedelta(hours=24)
            )
            
            assert job_id is not None, "Job ID should be returned"
            assert "followup_" in job_id, "Job ID should have correct format"
            
            # Verify in database
            jobs = await self.scheduler.get_scheduled_followups(user_id=self.test_user_id)
            assert len(jobs) == 1, "Should have 1 scheduled follow-up"
            assert jobs[0].trigger_type == FollowUpTriggerType.POST_EVENT
            assert jobs[0].status == FollowUpStatus.PENDING
            
            logger.info(f"✓ PASSED: Post-event follow-up scheduled: {job_id}")
            return job_id
        
        job_id = self.loop.run_until_complete(run_test())
        assert job_id is not None
    
    def test_03_emotion_based_template_selection(self):
        """Test 3: Emotion-Based Template Selection"""
        logger.info("\nTEST 3: Emotion-Based Template Selection")
        
        async def run_test():
            # Test high emotion (should use enthusiastic template)
            conv_id_high = f"{self.test_conv_id}_high"
            msg_high = await self.memory.store_message(
                conversation_id=conv_id_high,
                role=MessageRole.USER,
                content="Amazing service!",
                user_id=f"{self.test_user_id}_high",  # Use same user_id as in schedule call
                emotion_score=0.95,
                emotion_label="positive"
            )
            logger.info(f"Stored high emotion message: {msg_high.id if msg_high else 'FAILED'}")
            
            event_date = datetime.utcnow() + timedelta(days=1)
            job_id_high = await self.scheduler.schedule_post_event_followup(
                conversation_id=conv_id_high,
                user_id=f"{self.test_user_id}_high",
                event_date=event_date
            )
            
            # Test low emotion (should use empathetic template)
            conv_id_low = f"{self.test_conv_id}_low"
            msg_low = await self.memory.store_message(
                conversation_id=conv_id_low,
                role=MessageRole.USER,
                content="I have concerns",
                user_id=f"{self.test_user_id}_low",  # Use same user_id as in schedule call
                emotion_score=0.2,
                emotion_label="negative"
            )
            logger.info(f"Stored low emotion message: {msg_low.id if msg_low else 'FAILED'}")
            
            job_id_low = await self.scheduler.schedule_post_event_followup(
                conversation_id=conv_id_low,
                user_id=f"{self.test_user_id}_low",
                event_date=event_date
            )
            
            # Verify templates - get specific jobs by ID
            jobs = await self.scheduler.get_scheduled_followups()
            high_job = next((j for j in jobs if j.id == job_id_high), None)
            low_job = next((j for j in jobs if j.id == job_id_low), None)
            
            # Debug output
            logger.info(f"High emotion job: {high_job.template_id if high_job else 'NOT FOUND'}")
            logger.info(f"Low emotion job: {low_job.template_id if low_job else 'NOT FOUND'}")
            
            assert high_job is not None, f"High emotion job not found: {job_id_high}"
            assert low_job is not None, f"Low emotion job not found: {job_id_low}"
            assert high_job.template_id == "post_event_high_emotion", f"Expected post_event_high_emotion, got {high_job.template_id}"
            assert low_job.template_id == "post_event_low_emotion", f"Expected post_event_low_emotion, got {low_job.template_id}"
            
            logger.info("✓ PASSED: Emotion-based templates selected correctly")
        
        self.loop.run_until_complete(run_test())
    
    def test_04_schedule_reengagement(self):
        """Test 4: Schedule Re-Engagement Campaign"""
        logger.info("\nTEST 4: Schedule Re-Engagement Campaign")
        
        async def run_test():
            # Schedule re-engagement for user inactive for 30 days
            last_activity = datetime.utcnow() - timedelta(days=25)
            job_id = await self.scheduler.schedule_reengagement(
                user_id=f"{self.test_user_id}_reeng",
                last_activity=last_activity,
                inactive_threshold=timedelta(days=30)
            )
            
            assert job_id is not None, "Job ID should be returned"
            
            # Verify in database
            jobs = await self.scheduler.get_scheduled_followups(
                user_id=f"{self.test_user_id}_reeng"
            )
            assert len(jobs) == 1, "Should have 1 scheduled re-engagement"
            assert jobs[0].trigger_type == FollowUpTriggerType.RE_ENGAGEMENT
            
            logger.info(f"✓ PASSED: Re-engagement scheduled: {job_id}")
            return job_id
        
        job_id = self.loop.run_until_complete(run_test())
        assert job_id is not None
    
    def test_05_duplicate_prevention(self):
        """Test 5: Duplicate Follow-Up Prevention"""
        logger.info("\nTEST 5: Duplicate Follow-Up Prevention")
        
        async def run_test():
            event_date = datetime.utcnow() + timedelta(days=3)
            user_id = f"{self.test_user_id}_dup"
            
            # Schedule first follow-up
            job_id_1 = await self.scheduler.schedule_post_event_followup(
                conversation_id=f"{self.test_conv_id}_dup",
                user_id=user_id,
                event_date=event_date
            )
            
            assert job_id_1 is not None, "First job should be created"
            
            # Try to schedule duplicate (same event date)
            job_id_2 = await self.scheduler.schedule_post_event_followup(
                conversation_id=f"{self.test_conv_id}_dup2",
                user_id=user_id,
                event_date=event_date
            )
            
            assert job_id_2 is None, "Duplicate should be prevented"
            
            # Verify only one job exists
            jobs = await self.scheduler.get_scheduled_followups(user_id=user_id)
            assert len(jobs) == 1, "Should have only 1 follow-up"
            
            logger.info("✓ PASSED: Duplicate prevention working")
        
        self.loop.run_until_complete(run_test())
    
    def test_06_cancel_followup(self):
        """Test 6: Cancel Scheduled Follow-Up"""
        logger.info("\nTEST 6: Cancel Scheduled Follow-Up")
        
        async def run_test():
            # Schedule follow-up
            event_date = datetime.utcnow() + timedelta(days=4)
            user_id = f"{self.test_user_id}_cancel"
            
            job_id = await self.scheduler.schedule_post_event_followup(
                conversation_id=f"{self.test_conv_id}_cancel",
                user_id=user_id,
                event_date=event_date
            )
            
            assert job_id is not None, "Job should be created"
            
            # Cancel the follow-up
            result = await self.scheduler.cancel_followup(job_id)
            assert result is True, "Cancellation should succeed"
            
            # Verify status
            jobs = await self.scheduler.get_scheduled_followups(user_id=user_id)
            assert len(jobs) == 1, "Job should still exist"
            assert jobs[0].status == FollowUpStatus.CANCELLED, "Status should be cancelled"
            
            logger.info("✓ PASSED: Follow-up cancelled successfully")
        
        self.loop.run_until_complete(run_test())
    
    def test_07_list_scheduled_followups(self):
        """Test 7: List Scheduled Follow-Ups"""
        logger.info("\nTEST 7: List Scheduled Follow-Ups")
        
        async def run_test():
            user_id = f"{self.test_user_id}_list"
            
            # Schedule multiple follow-ups with well-separated dates
            event_date_1 = datetime.utcnow() + timedelta(days=5)
            event_date_2 = datetime.utcnow() + timedelta(days=10)  # Changed from 6 to 10 to avoid duplicate detection
            
            job_id_1 = await self.scheduler.schedule_post_event_followup(
                conversation_id=f"{self.test_conv_id}_list1",
                user_id=user_id,
                event_date=event_date_1
            )
            
            job_id_2 = await self.scheduler.schedule_post_event_followup(
                conversation_id=f"{self.test_conv_id}_list2",
                user_id=user_id,
                event_date=event_date_2
            )
            
            logger.info(f"Scheduled job_id_1: {job_id_1}, job_id_2: {job_id_2}")
            
            # List all for user
            jobs = await self.scheduler.get_scheduled_followups(user_id=user_id)
            logger.info(f"Found {len(jobs)} jobs for user {user_id}: {[j.id for j in jobs]}")
            assert len(jobs) >= 2, f"Should have at least 2 follow-ups, got {len(jobs)}"
            
            # List by status
            pending_jobs = await self.scheduler.get_scheduled_followups(
                user_id=user_id,
                status=FollowUpStatus.PENDING
            )
            logger.info(f"Found {len(pending_jobs)} pending jobs")
            assert len(pending_jobs) >= 2, f"Should have at least 2 pending, got {len(pending_jobs)}"
            
            logger.info(f"✓ PASSED: Listed {len(jobs)} follow-ups")
        
        self.loop.run_until_complete(run_test())
    
    def test_08_timezone_handling(self):
        """Test 8: Timezone Handling"""
        logger.info("\nTEST 8: Timezone Handling")
        
        async def run_test():
            # Create scheduler with specific timezone
            scheduler_pst = FollowUpScheduler(
                self.memory,
                self.emotion_service,
                timezone='US/Pacific'
            )
            await scheduler_pst.start()
            
            try:
                # Schedule follow-up
                event_date = datetime.utcnow() + timedelta(days=7)
                user_id = f"{self.test_user_id}_tz"
                
                job_id = await scheduler_pst.schedule_post_event_followup(
                    conversation_id=f"{self.test_conv_id}_tz",
                    user_id=user_id,
                    event_date=event_date
                )
                
                assert job_id is not None, "Job should be created with timezone"
                
                # Verify job exists
                jobs = await scheduler_pst.get_scheduled_followups(user_id=user_id)
                assert len(jobs) == 1, "Should have 1 follow-up"
                
                logger.info("✓ PASSED: Timezone handling working")
            finally:
                await scheduler_pst.stop()
        
        self.loop.run_until_complete(run_test())
    
    def test_09_health_check(self):
        """Test 9: Scheduler Health Check"""
        logger.info("\nTEST 9: Scheduler Health Check")
        
        async def run_test():
            health = await self.scheduler.health_check()
            
            assert health["status"] == "healthy", "Should be healthy"
            assert "scheduler_running" in health
            assert "pending_jobs" in health
            assert "executed_today" in health
            assert "apscheduler_jobs" in health
            
            logger.info(f"✓ PASSED: Health check: {health}")
        
        self.loop.run_until_complete(run_test())
    
    def test_10_message_template_rendering(self):
        """Test 10: Message Template Rendering"""
        logger.info("\nTEST 10: Message Template Rendering")
        
        async def run_test():
            # Schedule follow-up with event date
            event_date = datetime(2025, 11, 15, 18, 0, 0)
            user_id = f"{self.test_user_id}_template"
            
            # Add emotion history
            conv_id = f"{self.test_conv_id}_template"
            await self.memory.store_message(
                conversation_id=conv_id,
                role=MessageRole.USER,
                content="Great service!",
                user_id=user_id,
                emotion_score=0.8,
                emotion_label="positive"
            )
            
            job_id = await self.scheduler.schedule_post_event_followup(
                conversation_id=conv_id,
                user_id=user_id,
                event_date=event_date
            )
            
            # Get the scheduled job
            jobs = await self.scheduler.get_scheduled_followups(user_id=user_id)
            job = jobs[0]
            
            # Verify template has been rendered with event date
            assert job.message_preview is not None, "Should have message preview"
            assert "November 15, 2025" in job.message_preview, "Should have formatted date"
            
            logger.info(f"✓ PASSED: Template rendered: {job.message_preview[:100]}")
        
        self.loop.run_until_complete(run_test())


def run_tests():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("FOLLOW-UP SCHEDULER TEST SUITE")
    logger.info("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFollowUpScheduler)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("=" * 80)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failed: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        logger.info("✅ ALL TESTS PASSED")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
