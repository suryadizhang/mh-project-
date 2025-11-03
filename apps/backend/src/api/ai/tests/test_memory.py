"""
Memory Backend Tests
===================

Comprehensive test suite for conversation memory backends.

Tests:
- PostgreSQL memory operations
- Cross-channel conversation retrieval
- Emotion tracking and trend analysis
- Context window management
- Statistics and analytics
- Factory pattern and backend swapping

Run:
    cd apps/backend
    export PYTHONPATH=$PWD/src
    python src/api/ai/tests/test_memory.py
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import List

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import memory components
from api.ai.memory import (
    create_memory_backend,
    MemoryBackendType,
    MessageRole,
    ConversationChannel,
    ConversationMessage
)


# =============================================================================
# TEST SUITE
# =============================================================================

class MemoryBackendTests:
    """Comprehensive memory backend test suite"""
    
    def __init__(self):
        self.memory = None
        self.test_conv_id = f"test_conv_{datetime.now().timestamp()}"
        self.test_user_id = f"test_user_{datetime.now().timestamp()}"
    
    async def setup(self):
        """Initialize memory backend"""
        logger.info("Setting up memory backend for tests...")
        self.memory = await create_memory_backend(MemoryBackendType.POSTGRESQL)
        logger.info("✓ Memory backend initialized")
    
    async def teardown(self):
        """Cleanup"""
        if self.memory:
            await self.memory.close()
            logger.info("✓ Memory backend closed")
    
    # =========================================================================
    # TEST 1: Store and Retrieve Messages
    # =========================================================================
    
    async def test_store_and_retrieve(self):
        """Test basic message storage and retrieval"""
        print("\n" + "="*80)
        print("TEST 1: Store and Retrieve Messages")
        print("="*80)
        
        try:
            # Store user message
            msg1 = await self.memory.store_message(
                conversation_id=self.test_conv_id,
                role=MessageRole.USER,
                content="How much for 50 people?",
                channel=ConversationChannel.WEB,
                user_id=self.test_user_id
            )
            print(f"✓ Stored user message: {msg1.id}")
            
            # Store assistant message
            msg2 = await self.memory.store_message(
                conversation_id=self.test_conv_id,
                role=MessageRole.ASSISTANT,
                content="For 50 people, our Standard package costs $2,500...",
                channel=ConversationChannel.WEB,
                user_id=self.test_user_id
            )
            print(f"✓ Stored assistant message: {msg2.id}")
            
            # Retrieve conversation history
            history = await self.memory.get_conversation_history(self.test_conv_id)
            print(f"✓ Retrieved {len(history)} messages")
            
            # Verify
            assert len(history) == 2, f"Expected 2 messages, got {len(history)}"
            assert history[0].role == MessageRole.USER
            assert history[1].role == MessageRole.ASSISTANT
            assert "50 people" in history[0].content
            
            print("✓ TEST 1 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 1 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 2: Emotion Tracking
    # =========================================================================
    
    async def test_emotion_tracking(self):
        """Test emotion score tracking and trend analysis"""
        print("\n" + "="*80)
        print("TEST 2: Emotion Tracking")
        print("="*80)
        
        try:
            conv_id = f"{self.test_conv_id}_emotion"
            
            # Store messages with emotion scores
            emotions = [
                (0.2, "negative", ["frustration", "anger"]),
                (0.4, "neutral", []),
                (0.6, "positive", ["satisfaction"]),
                (0.8, "positive", ["joy", "excitement"])
            ]
            
            for i, (score, label, detected) in enumerate(emotions):
                await self.memory.store_message(
                    conversation_id=conv_id,
                    role=MessageRole.USER,
                    content=f"Message {i+1}",
                    user_id=self.test_user_id,
                    emotion_score=score,
                    emotion_label=label,
                    detected_emotions=detected
                )
                print(f"✓ Stored message with emotion: {label} ({score})")
            
            # Get emotion history
            emotion_history = await self.memory.get_emotion_history(conv_id, limit=10)
            print(f"✓ Retrieved {len(emotion_history)} emotion records")
            
            # Verify trend
            assert len(emotion_history) == 4
            assert emotion_history[0]["score"] == 0.2  # Oldest first
            assert emotion_history[-1]["score"] == 0.8  # Newest last
            
            # Get conversation metadata
            metadata = await self.memory.get_conversation_metadata(conv_id)
            print(f"✓ Average emotion score: {metadata.average_emotion_score:.2f}")
            print(f"✓ Emotion trend: {metadata.emotion_trend}")
            
            # Verify trend calculation
            assert metadata.emotion_trend == "improving", f"Expected 'improving', got '{metadata.emotion_trend}'"
            assert metadata.average_emotion_score > 0.4
            
            print("✓ TEST 2 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 2 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 3: Escalation Detection
    # =========================================================================
    
    async def test_escalation(self):
        """Test conversation escalation for negative emotions"""
        print("\n" + "="*80)
        print("TEST 3: Escalation Detection")
        print("="*80)
        
        try:
            conv_id = f"{self.test_conv_id}_escalation"
            
            # Store message with very negative emotion
            await self.memory.store_message(
                conversation_id=conv_id,
                role=MessageRole.USER,
                content="I'm absolutely furious! This is unacceptable!",
                user_id=self.test_user_id,
                emotion_score=0.1,
                emotion_label="negative",
                detected_emotions=["anger", "frustration", "dissatisfaction"]
            )
            print("✓ Stored message with negative emotion (score: 0.1)")
            
            # Mark conversation as escalated
            await self.memory.update_conversation_metadata(
                conversation_id=conv_id,
                escalated=True
            )
            print("✓ Marked conversation as escalated")
            
            # Verify escalation
            metadata = await self.memory.get_conversation_metadata(conv_id)
            assert metadata.escalated == True, "Conversation should be escalated"
            assert metadata.escalated_at is not None, "Escalation timestamp should be set"
            print(f"✓ Escalated at: {metadata.escalated_at}")
            
            # Get escalated conversations
            escalated = await self.memory.get_escalated_conversations(hours=1)
            print(f"✓ Found {len(escalated)} escalated conversations in last hour")
            assert len(escalated) >= 1, "Should find at least one escalated conversation"
            
            print("✓ TEST 3 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 3 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 4: Cross-Channel Conversation
    # =========================================================================
    
    async def test_cross_channel(self):
        """Test conversation across multiple channels"""
        print("\n" + "="*80)
        print("TEST 4: Cross-Channel Conversation")
        print("="*80)
        
        try:
            user_id = f"{self.test_user_id}_multichannel"
            
            # Simulate user conversation across multiple channels
            channels = [
                (ConversationChannel.WEB, "I'm interested in catering"),
                (ConversationChannel.EMAIL, "Following up on my inquiry"),
                (ConversationChannel.SMS, "Are you available next week?")
            ]
            
            for channel, content in channels:
                conv_id = f"{self.test_conv_id}_{channel.value}"
                await self.memory.store_message(
                    conversation_id=conv_id,
                    role=MessageRole.USER,
                    content=content,
                    channel=channel,
                    user_id=user_id
                )
                print(f"✓ Stored message on {channel.value}: {content}")
            
            # Get user's history across all channels
            user_history = await self.memory.get_user_history(
                user_id=user_id,
                limit=10
            )
            print(f"✓ Retrieved {len(user_history)} messages across all channels")
            
            # Verify all channels present
            assert len(user_history) == 3, f"Expected 3 messages, got {len(user_history)}"
            channels_found = set(msg.channel for msg in user_history)
            assert len(channels_found) == 3, f"Expected 3 channels, got {len(channels_found)}"
            print(f"✓ Channels found: {[ch.value for ch in channels_found]}")
            
            # Get user's conversations
            conversations = await self.memory.get_user_conversations(user_id)
            print(f"✓ Found {len(conversations)} conversations for user")
            assert len(conversations) == 3, f"Expected 3 conversations, got {len(conversations)}"
            
            print("✓ TEST 4 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 4 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 5: Context Window Management
    # =========================================================================
    
    async def test_context_window(self):
        """Test context window for token budget management"""
        print("\n" + "="*80)
        print("TEST 5: Context Window Management")
        print("="*80)
        
        try:
            conv_id = f"{self.test_conv_id}_context"
            
            # Store many messages
            for i in range(20):
                content = f"Message {i+1}: " + "This is a test message. " * 10  # ~100 chars
                await self.memory.store_message(
                    conversation_id=conv_id,
                    role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                    content=content,
                    user_id=self.test_user_id
                )
            print("✓ Stored 20 messages (~2000 characters total)")
            
            # Get context window with token budget
            context = await self.memory.get_context_window(
                conversation_id=conv_id,
                max_tokens=1000  # Should fit ~8-10 messages
            )
            print(f"✓ Retrieved {len(context)} messages within token budget")
            
            # Verify context fits budget
            total_chars = sum(len(msg.content) for msg in context)
            estimated_tokens = total_chars // 4
            print(f"✓ Estimated tokens: {estimated_tokens} (budget: 1000)")
            
            assert len(context) < 20, "Should not return all messages"
            assert len(context) > 0, "Should return some messages"
            assert estimated_tokens <= 1100, "Should stay within token budget (with margin)"
            
            # Verify chronological order
            for i in range(len(context) - 1):
                assert context[i].timestamp <= context[i+1].timestamp, "Messages should be chronological"
            
            print("✓ TEST 5 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 5 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 6: Recent Messages
    # =========================================================================
    
    async def test_recent_messages(self):
        """Test retrieving recent messages efficiently"""
        print("\n" + "="*80)
        print("TEST 6: Recent Messages")
        print("="*80)
        
        try:
            conv_id = f"{self.test_conv_id}_recent"
            
            # Store 15 messages
            for i in range(15):
                await self.memory.store_message(
                    conversation_id=conv_id,
                    role=MessageRole.USER,
                    content=f"Message {i+1}",
                    user_id=self.test_user_id
                )
            print("✓ Stored 15 messages")
            
            # Get 10 most recent
            recent = await self.memory.get_recent_messages(conv_id, count=10)
            print(f"✓ Retrieved {len(recent)} recent messages")
            
            # Verify
            assert len(recent) == 10, f"Expected 10 messages, got {len(recent)}"
            assert "Message 6" in recent[0].content, "Should start with message 6"
            assert "Message 15" in recent[-1].content, "Should end with message 15"
            
            print("✓ TEST 6 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 6 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 7: Conversation Lifecycle
    # =========================================================================
    
    async def test_conversation_lifecycle(self):
        """Test conversation creation, update, and closure"""
        print("\n" + "="*80)
        print("TEST 7: Conversation Lifecycle")
        print("="*80)
        
        try:
            conv_id = f"{self.test_conv_id}_lifecycle"
            
            # Create conversation by storing message
            await self.memory.store_message(
                conversation_id=conv_id,
                role=MessageRole.USER,
                content="Start conversation",
                user_id=self.test_user_id
            )
            print("✓ Created conversation")
            
            # Get metadata
            metadata = await self.memory.get_conversation_metadata(conv_id)
            assert metadata.is_active == True, "New conversation should be active"
            assert metadata.message_count == 1, "Should have 1 message"
            print(f"✓ Conversation active, {metadata.message_count} messages")
            
            # Update context
            await self.memory.update_conversation_metadata(
                conversation_id=conv_id,
                context={"booking_id": "BK123", "event_date": "2025-12-20"}
            )
            print("✓ Updated conversation context")
            
            # Verify context
            metadata = await self.memory.get_conversation_metadata(conv_id)
            assert "booking_id" in metadata.context
            print(f"✓ Context: {metadata.context}")
            
            # Close conversation
            await self.memory.close_conversation(conv_id, reason="completed")
            print("✓ Closed conversation")
            
            # Verify closure
            metadata = await self.memory.get_conversation_metadata(conv_id)
            assert metadata.is_active == False, "Conversation should be inactive"
            assert metadata.closed_at is not None, "Should have closed timestamp"
            assert metadata.closed_reason == "completed"
            print(f"✓ Closed at: {metadata.closed_at}, Reason: {metadata.closed_reason}")
            
            print("✓ TEST 7 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 7 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 8: Statistics and Analytics
    # =========================================================================
    
    async def test_statistics(self):
        """Test statistics and analytics"""
        print("\n" + "="*80)
        print("TEST 8: Statistics and Analytics")
        print("="*80)
        
        try:
            # Get overall statistics
            stats = await self.memory.get_statistics(days=30)
            print(f"✓ Total conversations: {stats['total_conversations']}")
            print(f"✓ Total messages: {stats['total_messages']}")
            print(f"✓ Active conversations: {stats['active_conversations']}")
            print(f"✓ Average emotion score: {stats['average_emotion_score']:.2f}")
            print(f"✓ Escalation rate: {stats['escalation_rate']:.2%}")
            print(f"✓ Channels: {stats['channels']}")
            
            # Verify statistics structure
            assert "total_conversations" in stats
            assert "total_messages" in stats
            assert "average_emotion_score" in stats
            assert "channels" in stats
            assert isinstance(stats["channels"], dict)
            
            print("✓ TEST 8 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 8 FAILED: {e}")
            return False
    
    # =========================================================================
    # TEST 9: Health Check
    # =========================================================================
    
    async def test_health_check(self):
        """Test backend health check"""
        print("\n" + "="*80)
        print("TEST 9: Health Check")
        print("="*80)
        
        try:
            health = await self.memory.health_check()
            print(f"✓ Status: {health['status']}")
            print(f"✓ Backend: {health['backend']}")
            print(f"✓ Latency: {health['latency_ms']}ms")
            print(f"✓ Message count: {health.get('message_count', 'N/A')}")
            
            # Verify health structure
            assert health["status"] in ["healthy", "degraded", "unhealthy", "stub"]
            assert health["backend"] in ["postgresql", "neo4j"]
            assert "latency_ms" in health
            
            print("✓ TEST 9 PASSED")
            return True
            
        except Exception as e:
            print(f"✗ TEST 9 FAILED: {e}")
            return False


# =============================================================================
# TEST RUNNER
# =============================================================================

async def run_all_tests():
    """Run comprehensive memory backend tests"""
    
    print("\n" + "="*80)
    print("MEMORY BACKEND TEST SUITE")
    print("="*80)
    print(f"Testing PostgreSQL memory backend")
    print(f"Time: {datetime.now()}")
    print("="*80)
    
    suite = MemoryBackendTests()
    
    try:
        # Setup
        await suite.setup()
        
        # Run tests
        tests = [
            suite.test_store_and_retrieve,
            suite.test_emotion_tracking,
            suite.test_escalation,
            suite.test_cross_channel,
            suite.test_context_window,
            suite.test_recent_messages,
            suite.test_conversation_lifecycle,
            suite.test_statistics,
            suite.test_health_check
        ]
        
        results = []
        for test in tests:
            result = await test()
            results.append(result)
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        passed = sum(results)
        total = len(results)
        
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n✅ ALL TESTS PASSED")
        else:
            print(f"\n❌ {total - passed} TESTS FAILED")
        
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Teardown
        await suite.teardown()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    asyncio.run(run_all_tests())
