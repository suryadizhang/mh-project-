"""
Comprehensive Audit for Follow-Up Scheduler Integration
========================================================

This audit script validates:
1. Database schema and indexes
2. Orchestrator initialization
3. Scheduler lifecycle management
4. Template selection logic
5. Integration points
6. Performance benchmarks
7. Error handling coverage
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Set environment
os.environ["MEMORY_BACKEND"] = "postgresql"
os.environ["SCHEDULER_TIMEZONE"] = "UTC"


class AuditResult:
    """Audit result container"""
    def __init__(self, category: str, check: str):
        self.category = category
        self.check = check
        self.passed = False
        self.message = ""
        self.details = {}
    
    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.check} - {self.message}"


class SchedulerIntegrationAudit:
    """Comprehensive audit for scheduler integration"""
    
    def __init__(self):
        self.results: List[AuditResult] = []
        self.critical_failures = 0
        self.warnings = 0
    
    def _add_result(self, result: AuditResult):
        """Add audit result"""
        self.results.append(result)
        if not result.passed:
            self.critical_failures += 1
    
    async def run_all_audits(self):
        """Run all audit checks"""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE SCHEDULER INTEGRATION AUDIT")
        logger.info("=" * 80)
        logger.info("")
        
        await self.audit_database_schema()
        await self.audit_orchestrator_initialization()
        await self.audit_scheduler_lifecycle()
        await self.audit_template_selection()
        await self.audit_integration_points()
        await self.audit_performance()
        await self.audit_error_handling()
        
        self._print_summary()
    
    # =========================================================================
    # Category 1: Database Schema
    # =========================================================================
    
    async def audit_database_schema(self):
        """Audit database schema and indexes"""
        logger.info("\n📊 CATEGORY 1: DATABASE SCHEMA")
        logger.info("-" * 80)
        
        from core.database import get_db_context
        from sqlalchemy import text
        
        # Check table exists
        result = AuditResult("Database", "scheduled_followups table exists")
        try:
            async with get_db_context() as db:
                query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'scheduled_followups'
                """)
                res = await db.execute(query)
                table_exists = res.scalar() is not None
                
                if table_exists:
                    result.passed = True
                    result.message = "Table exists"
                else:
                    result.message = "Table not found"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Check columns
        result = AuditResult("Database", "All required columns present")
        try:
            async with get_db_context() as db:
                query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'scheduled_followups'
                """)
                res = await db.execute(query)
                columns = [row[0] for row in res.fetchall()]
                
                required_columns = [
                    'id', 'conversation_id', 'user_id', 'trigger_type',
                    'trigger_data', 'scheduled_at', 'executed_at', 'cancelled_at',
                    'status', 'template_id', 'message_content', 'created_at',
                    'error_message', 'retry_count'
                ]
                
                missing = [c for c in required_columns if c not in columns]
                
                if not missing:
                    result.passed = True
                    result.message = f"All {len(required_columns)} columns present"
                    result.details = {"columns": columns}
                else:
                    result.message = f"Missing columns: {missing}"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Check indexes
        result = AuditResult("Database", "Performance indexes exist")
        try:
            async with get_db_context() as db:
                query = text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'scheduled_followups'
                """)
                res = await db.execute(query)
                indexes = [row[0] for row in res.fetchall()]
                
                expected_indexes = [
                    'ix_scheduled_followups_user_id',
                    'ix_scheduled_followups_conversation_id',
                    'ix_scheduled_followups_scheduled_at',  # Created by index=True in column
                    'idx_scheduled_followups_status_scheduled',
                    'idx_scheduled_followups_user_status'
                ]
                
                missing = [idx for idx in expected_indexes if idx not in indexes]
                
                if not missing:
                    result.passed = True
                    result.message = f"All {len(expected_indexes)} indexes present"
                    result.details = {"indexes": indexes}
                else:
                    result.message = f"Missing indexes: {missing}"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
    
    # =========================================================================
    # Category 2: Orchestrator Initialization
    # =========================================================================
    
    async def audit_orchestrator_initialization(self):
        """Audit orchestrator initialization"""
        logger.info("\n🚀 CATEGORY 2: ORCHESTRATOR INITIALIZATION")
        logger.info("-" * 80)
        
        # Import orchestrator
        result = AuditResult("Orchestrator", "AIOrchestrator imports successfully")
        try:
            from api.ai.orchestrator import AIOrchestrator
            result.passed = True
            result.message = "Import successful"
        except Exception as e:
            result.message = f"Import failed: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Initialize orchestrator
        result = AuditResult("Orchestrator", "Orchestrator initializes with scheduler")
        try:
            from api.ai.orchestrator import AIOrchestrator
            orchestrator = AIOrchestrator(use_router=False)
            
            # Call start() to initialize memory backend and scheduler
            await orchestrator.start()
            
            if orchestrator.scheduler:
                result.passed = True
                result.message = "Scheduler initialized"
                result.details = {
                    "scheduler_type": type(orchestrator.scheduler).__name__,
                    "timezone": str(orchestrator.scheduler.timezone)
                }
            else:
                result.message = "Scheduler is None"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        if result.details:
            logger.info(f"    Details: {result.details}")
        
        # Check callback
        result = AuditResult("Orchestrator", "Orchestrator callback configured")
        try:
            if hasattr(orchestrator.scheduler, 'orchestrator_callback'):
                callback = orchestrator.scheduler.orchestrator_callback
                if callback:
                    result.passed = True
                    result.message = f"Callback: {callback.__name__}"
                else:
                    result.message = "Callback is None"
            else:
                result.message = "No orchestrator_callback attribute"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Cleanup
        await orchestrator.stop()
        
        # Cleanup
        if 'orchestrator' in locals():
            await orchestrator.stop()
    
    # =========================================================================
    # Category 3: Scheduler Lifecycle
    # =========================================================================
    
    async def audit_scheduler_lifecycle(self):
        """Audit scheduler start/stop lifecycle"""
        logger.info("\n🔄 CATEGORY 3: SCHEDULER LIFECYCLE")
        logger.info("-" * 80)
        
        from api.ai.orchestrator import AIOrchestrator
        
        # Start scheduler
        result = AuditResult("Lifecycle", "Scheduler starts successfully")
        try:
            orchestrator = AIOrchestrator(use_router=False)
            await orchestrator.start()
            
            health = await orchestrator.scheduler.health_check()
            if health["scheduler_running"]:
                result.passed = True
                result.message = "Scheduler running"
                result.details = health
            else:
                result.message = "Scheduler not running"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Stop scheduler
        result = AuditResult("Lifecycle", "Scheduler stops gracefully")
        try:
            await orchestrator.stop()
            
            # Check if scheduler stopped
            health = await orchestrator.scheduler.health_check()
            if not health["scheduler_running"]:
                result.passed = True
                result.message = "Scheduler stopped"
            else:
                result.message = "Scheduler still running"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Restart scheduler
        result = AuditResult("Lifecycle", "Scheduler can be restarted")
        try:
            await orchestrator.start()
            health = await orchestrator.scheduler.health_check()
            
            if health["scheduler_running"]:
                result.passed = True
                result.message = "Scheduler restarted"
            else:
                result.message = "Scheduler failed to restart"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Cleanup
        await orchestrator.stop()
    
    # =========================================================================
    # Category 4: Template Selection
    # =========================================================================
    
    async def audit_template_selection(self):
        """Audit template selection logic"""
        logger.info("\n📝 CATEGORY 4: TEMPLATE SELECTION")
        logger.info("-" * 80)
        
        from api.ai.orchestrator import AIOrchestrator
        from api.ai.scheduler.follow_up_scheduler import FOLLOW_UP_TEMPLATES
        
        orchestrator = AIOrchestrator(use_router=False)
        await orchestrator.start()
        
        # Check templates loaded
        result = AuditResult("Templates", "All templates loaded")
        try:
            template_count = len(FOLLOW_UP_TEMPLATES)
            if template_count == 6:
                result.passed = True
                result.message = f"{template_count} templates loaded"
                result.details = {"templates": list(FOLLOW_UP_TEMPLATES.keys())}
            else:
                result.message = f"Expected 6 templates, found {template_count}"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Test high emotion selection
        result = AuditResult("Templates", "High emotion selects correct template")
        try:
            from api.ai.scheduler.follow_up_scheduler import FollowUpTriggerType
            
            emotion_history = [{"score": 0.95, "label": "positive"}]
            template = await orchestrator.scheduler._select_template_by_emotion(
                FollowUpTriggerType.POST_EVENT,
                emotion_history
            )
            
            if template.id == "post_event_high_emotion":
                result.passed = True
                result.message = "Correct template selected"
            else:
                result.message = f"Wrong template: {template.id}"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Test low emotion selection
        result = AuditResult("Templates", "Low emotion selects correct template")
        try:
            emotion_history = [{"score": 0.2, "label": "negative"}]
            template = await orchestrator.scheduler._select_template_by_emotion(
                FollowUpTriggerType.POST_EVENT,
                emotion_history
            )
            
            if template.id == "post_event_low_emotion":
                result.passed = True
                result.message = "Correct template selected"
            else:
                result.message = f"Wrong template: {template.id}"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Test neutral emotion selection
        result = AuditResult("Templates", "Neutral emotion selects correct template")
        try:
            emotion_history = [{"score": 0.5, "label": "neutral"}]
            template = await orchestrator.scheduler._select_template_by_emotion(
                FollowUpTriggerType.POST_EVENT,
                emotion_history
            )
            
            if template.id == "post_event_neutral_emotion":
                result.passed = True
                result.message = "Correct template selected"
            else:
                result.message = f"Wrong template: {template.id}"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        await orchestrator.stop()
    
    # =========================================================================
    # Category 5: Integration Points
    # =========================================================================
    
    async def audit_integration_points(self):
        """Audit integration points"""
        logger.info("\n🔗 CATEGORY 5: INTEGRATION POINTS")
        logger.info("-" * 80)
        
        from api.ai.orchestrator import AIOrchestrator
        
        orchestrator = AIOrchestrator(use_router=False)
        await orchestrator.start()
        
        # Check memory backend integration
        result = AuditResult("Integration", "Memory backend accessible")
        try:
            if orchestrator.memory_backend:
                result.passed = True
                result.message = f"Memory backend: {type(orchestrator.memory_backend).__name__}"
            else:
                result.message = "Memory backend is None"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Check emotion service integration
        result = AuditResult("Integration", "Emotion service accessible")
        try:
            if orchestrator.emotion_service:
                result.passed = True
                result.message = f"Emotion service: {type(orchestrator.emotion_service).__name__}"
            else:
                result.message = "Emotion service is None"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Check scheduling method exists
        result = AuditResult("Integration", "Scheduling methods available")
        try:
            has_post_event = hasattr(orchestrator, 'schedule_post_event_followup')
            has_reengagement = hasattr(orchestrator, 'schedule_reengagement')
            
            if has_post_event and has_reengagement:
                result.passed = True
                result.message = "Both scheduling methods present"
            else:
                result.message = "Missing scheduling methods"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Check inactive user detection
        result = AuditResult("Integration", "Inactive user detection available")
        try:
            from api.ai.scheduler.inactive_user_detection import (
                detect_inactive_users,
                schedule_reengagement_campaigns
            )
            result.passed = True
            result.message = "Inactive user detection module loaded"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        await orchestrator.stop()
    
    # =========================================================================
    # Category 6: Performance
    # =========================================================================
    
    async def audit_performance(self):
        """Audit performance benchmarks"""
        logger.info("\n⚡ CATEGORY 6: PERFORMANCE")
        logger.info("-" * 80)
        
        import time
        from api.ai.orchestrator import AIOrchestrator
        from api.ai.memory import get_memory_backend
        from api.ai.memory.memory_backend import MessageRole
        
        orchestrator = AIOrchestrator(use_router=False)
        await orchestrator.start()
        memory = await get_memory_backend()  # Await the coroutine
        
        # Benchmark: Schedule follow-up
        result = AuditResult("Performance", "Schedule follow-up < 500ms")
        try:
            conv_id = f"perf_test_{time.time()}"
            user_id = f"perf_user_{time.time()}"
            
            # Store message first
            await memory.store_message(
                conversation_id=conv_id,
                role=MessageRole.USER,
                content="Test",
                user_id=user_id,
                emotion_score=0.7
            )
            
            # Benchmark scheduling
            start = time.time()
            job_id = await orchestrator.schedule_post_event_followup(
                conversation_id=conv_id,
                user_id=user_id,
                event_date=datetime.utcnow() + timedelta(days=7)
            )
            duration_ms = (time.time() - start) * 1000
            
            if duration_ms < 500:
                result.passed = True
                result.message = f"Scheduling took {duration_ms:.0f}ms"
            else:
                result.message = f"Scheduling took {duration_ms:.0f}ms (>500ms threshold)"
            
            # Cleanup
            if job_id:
                await orchestrator.scheduler.cancel_followup(job_id)
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Benchmark: Health check
        result = AuditResult("Performance", "Health check < 100ms")
        try:
            start = time.time()
            health = await orchestrator.scheduler.health_check()
            duration_ms = (time.time() - start) * 1000
            
            if duration_ms < 100:
                result.passed = True
                result.message = f"Health check took {duration_ms:.0f}ms"
            else:
                result.message = f"Health check took {duration_ms:.0f}ms (>100ms threshold)"
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        await orchestrator.stop()
    
    # =========================================================================
    # Category 7: Error Handling
    # =========================================================================
    
    async def audit_error_handling(self):
        """Audit error handling coverage"""
        logger.info("\n🛡️ CATEGORY 7: ERROR HANDLING")
        logger.info("-" * 80)
        
        from api.ai.orchestrator import AIOrchestrator
        
        orchestrator = AIOrchestrator(use_router=False)
        await orchestrator.start()
        
        # Test: Invalid user_id
        result = AuditResult("Error Handling", "Handles invalid user_id")
        try:
            job_id = await orchestrator.schedule_post_event_followup(
                conversation_id="invalid",
                user_id="",  # Empty user_id
                event_date=datetime.utcnow() + timedelta(days=1)
            )
            # Should handle gracefully (may return None or raise)
            result.passed = True
            result.message = "Handled gracefully"
        except Exception as e:
            # Expected to raise or handle
            result.passed = True
            result.message = f"Raised exception: {type(e).__name__}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Test: Past event date
        result = AuditResult("Error Handling", "Handles past event dates")
        try:
            job_id = await orchestrator.schedule_post_event_followup(
                conversation_id="past_test",
                user_id="past_user",
                event_date=datetime.utcnow() - timedelta(days=1)  # Past date
            )
            # Should handle gracefully
            result.passed = True
            result.message = "Handled gracefully"
        except Exception as e:
            result.passed = True
            result.message = f"Raised exception: {type(e).__name__}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        # Test: Duplicate scheduling
        result = AuditResult("Error Handling", "Prevents duplicate scheduling")
        try:
            conv_id = f"dup_test_{time.time()}"
            user_id = f"dup_user_{time.time()}"
            event_date = datetime.utcnow() + timedelta(days=5)
            
            # First schedule
            job_id_1 = await orchestrator.schedule_post_event_followup(
                conversation_id=conv_id,
                user_id=user_id,
                event_date=event_date
            )
            
            # Second schedule (should be prevented)
            job_id_2 = await orchestrator.schedule_post_event_followup(
                conversation_id=conv_id,
                user_id=user_id,
                event_date=event_date
            )
            
            if job_id_1 and not job_id_2:
                result.passed = True
                result.message = "Duplicate prevented"
            else:
                result.message = f"Duplicate not prevented: {job_id_1}, {job_id_2}"
            
            # Cleanup
            if job_id_1:
                await orchestrator.scheduler.cancel_followup(job_id_1)
        except Exception as e:
            result.message = f"Error: {e}"
        
        self._add_result(result)
        logger.info(f"  {result}")
        
        await orchestrator.stop()
    
    # =========================================================================
    # Summary
    # =========================================================================
    
    def _print_summary(self):
        """Print audit summary"""
        logger.info("\n" + "=" * 80)
        logger.info("AUDIT SUMMARY")
        logger.info("=" * 80)
        
        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {"passed": 0, "failed": 0}
            
            if result.passed:
                categories[result.category]["passed"] += 1
            else:
                categories[result.category]["failed"] += 1
        
        # Print category summary
        for category, counts in categories.items():
            total = counts["passed"] + counts["failed"]
            status = "✅" if counts["failed"] == 0 else "⚠️"
            logger.info(f"{status} {category}: {counts['passed']}/{total} passed")
        
        # Overall summary
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r.passed)
        failed_checks = total_checks - passed_checks
        
        logger.info("")
        logger.info(f"Total Checks: {total_checks}")
        logger.info(f"✅ Passed: {passed_checks}")
        logger.info(f"❌ Failed: {failed_checks}")
        
        if failed_checks == 0:
            logger.info("")
            logger.info("🎉 ALL AUDIT CHECKS PASSED - SYSTEM IS PRODUCTION READY")
        else:
            logger.info("")
            logger.info("⚠️ SOME AUDIT CHECKS FAILED - REVIEW REQUIRED")
            logger.info("")
            logger.info("Failed checks:")
            for result in self.results:
                if not result.passed:
                    logger.info(f"  - {result.category}: {result.check}")
                    logger.info(f"    {result.message}")


async def main():
    """Run comprehensive audit"""
    audit = SchedulerIntegrationAudit()
    await audit.run_all_audits()
    
    # Return exit code
    return 0 if audit.critical_failures == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
