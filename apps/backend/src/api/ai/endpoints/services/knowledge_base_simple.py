"""
Production Knowledge Base Service
Integrated with actual database and real business data
Supports AI chat with context from bookings, menu, reviews, and FAQs
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Any, List, Dict, Optional
from uuid import uuid4

from sqlalchemy import select, update, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ProductionKnowledgeBaseService:
    """Production-ready knowledge base integrated with real business data"""

    def __init__(self):
        self.chunks_cache = {}  # Redis-backed cache in production (fallback to memory for now)
        self.keywords_index = {}  # Fast keyword lookup
        logger.info("KnowledgeBase: Initializing production knowledge base service")
        
        # Load business configuration from settings
        self._load_business_knowledge()

    def _load_business_knowledge(self):
        """Load real business knowledge from settings"""
        business_knowledge = [
            # Restaurant Info - FROM SETTINGS
            {
                "content": f"{settings.BUSINESS_NAME} - {settings.APP_NAME}. We provide professional hibachi chef services. "
                          f"Contact us at {settings.BUSINESS_EMAIL} or {settings.BUSINESS_PHONE}. "
                          f"Service areas: {settings.SERVICE_AREAS}.",
                "keywords": ["business", "company", "contact", "email", "phone", "location", "service areas"],
                "category": "business_info",
                "priority": 10
            },
            
            # Booking Info
            {
                "content": "We offer hibachi chef booking services for private events, parties, and celebrations. "
                          "Bookings can be made online through our website or by calling our business phone. "
                          "We serve parties from small gatherings to large events. Payment accepted via Stripe, Plaid, or alternative methods.",
                "keywords": ["booking", "reservation", "event", "party", "celebration", "schedule", "date", "time"],
                "category": "booking_info",
                "priority": 9
            },
            
            # Payment Info - FROM SETTINGS
            {
                "content": f"Payment Options: Credit/Debit cards via Stripe, Bank transfers via Plaid, "
                          f"Zelle ({settings.ZELLE_EMAIL} or {settings.ZELLE_PHONE}), "
                          f"Venmo ({settings.VENMO_USERNAME}). "
                          f"We offer flexible payment options for your convenience. All payments are processed securely.",
                "keywords": ["payment", "stripe", "plaid", "bank transfer", "zelle", "venmo", "pay", "cost", "price", "money", "card", "credit", "debit"],
                "category": "payment_info",
                "priority": 8
            },

            # Payment Methods FAQ
            {
                "content": f"Payment Methods FAQ: We accept four secure payment options. "
                          f"1) Credit/Debit Cards - Processed securely via Stripe portal with instant confirmation. "
                          f"2) Bank Transfer - Direct bank payment via Plaid, secure and convenient. "
                          f"3) Zelle - Send to {settings.ZELLE_EMAIL} or {settings.ZELLE_PHONE} for instant transfer. "
                          f"4) Venmo - Pay {settings.VENMO_USERNAME} for quick and easy payment. "
                          f"All payment methods are secure, encrypted, and processed immediately.",
                "keywords": ["payment", "faq", "methods", "how to pay", "bank transfer", "plaid", "options", "ways to pay", "accepted payments"],
                "category": "faq_payment_methods",
                "priority": 9
            },
            
            # Service Description - FROM SETTINGS
            {
                "content": "Our professional hibachi chefs bring the authentic Japanese hibachi experience to your location. "
                          "We provide all equipment, fresh ingredients, and entertainment. Services include: "
                          "private parties, corporate events, birthday celebrations, weddings, and more.",
                "keywords": ["service", "chef", "hibachi", "japanese", "entertainment", "fresh", "ingredients", "professional"],
                "category": "service_info",
                "priority": 9
            },
            
            # FAQ - Cancellation
            {
                "content": "Cancellation Policy: Bookings can be cancelled up to 48 hours before the event for a full refund. "
                          "Cancellations within 48 hours may incur a cancellation fee. Contact customer service for special circumstances.",
                "keywords": ["cancel", "cancellation", "refund", "policy", "48 hours", "fee"],
                "category": "faq_cancellation",
                "priority": 7
            },
            
            # FAQ - Requirements
            {
                "content": "Requirements: We need access to electricity, a flat cooking surface area (table/counter), "
                          "and adequate space for the chef to perform. Outdoor events are possible with proper setup. "
                          "We bring all cooking equipment and supplies.",
                "keywords": ["requirements", "setup", "space", "electricity", "equipment", "outdoor", "indoor"],
                "category": "faq_requirements",
                "priority": 7
            },
            
            # FAQ - Group Size
            {
                "content": "We accommodate groups of all sizes, from intimate gatherings of 2 people to large events of 50+ guests. "
                          "Pricing varies based on group size and menu selection. Multiple chefs available for larger events.",
                "keywords": ["group", "size", "people", "guests", "capacity", "large", "small", "multiple"],
                "category": "faq_group_size",
                "priority": 7
            },
            
            # Reviews & Quality
            {
                "content": f"Customer reviews and feedback are important to us. After your event, you can leave a review "
                          f"on our website or on Yelp at {settings.YELP_REVIEW_URL}. "
                          f"Approved reviews may receive a {settings.REVIEW_COUPON_DISCOUNT_PERCENTAGE}% discount coupon for future bookings.",
                "keywords": ["review", "feedback", "rating", "yelp", "testimonial", "coupon", "discount"],
                "category": "reviews_quality",
                "priority": 6
            },
            
            # ===== ADMIN SYSTEM FEATURES =====
            
            # Admin Dashboard Features
            {
                "content": "Admin Dashboard provides: Revenue analytics with charts, booking statistics, payment tracking, "
                          "lead management with CRM, customer database, newsletter campaigns with templates, "
                          "SMS/email notifications, discount code management, SEO automation tools, and AI learning system. "
                          "Dashboard shows real-time metrics: total revenue, bookings this month, pending payments, conversion rates.",
                "keywords": ["dashboard", "admin", "analytics", "metrics", "revenue", "statistics", "reports", "overview"],
                "category": "admin_dashboard",
                "priority": 10
            },
            
            # Booking Management System
            {
                "content": "Booking Management: Admin can view all bookings in calendar/list view, filter by status "
                          "(pending/confirmed/completed/cancelled), manage booking details, assign chefs to events, "
                          "send confirmation emails, process payments, issue invoices, track booking sources, "
                          "and handle cancellations. System supports drag-and-drop scheduling on calendar view.",
                "keywords": ["booking", "management", "admin", "calendar", "schedule", "confirmation", "invoice", "status"],
                "category": "admin_bookings",
                "priority": 9
            },
            
            # CRM & Lead Management
            {
                "content": "CRM System: Lead pipeline with stages (New → Qualified → Converted), AI lead scoring (0-100), "
                          "lead source tracking (website, phone, social media, referral), follow-up calendar with reminders, "
                          "convert lead to booking with 1-click, kanban board for visual pipeline management, "
                          "auto-assign leads to sales team, track lead history and interactions.",
                "keywords": ["crm", "leads", "pipeline", "sales", "scoring", "conversion", "follow-up", "qualification"],
                "category": "admin_crm",
                "priority": 9
            },
            
            # Payment Processing
            {
                "content": "Payment System: Process payments via Stripe (cards), Plaid (bank transfers), "
                          "or manual (Zelle/Venmo/CashApp). Automatic payment detection from Gmail, "
                          "payment matching with bookings using AI, invoice generation, refund processing, "
                          "payment reminder emails, overdue payment tracking, payment history dashboard.",
                "keywords": ["payment", "processing", "stripe", "plaid", "invoice", "refund", "overdue", "transaction"],
                "category": "admin_payments",
                "priority": 9
            },
            
            # Customer Management
            {
                "content": "Customer Database: View all customers with contact info, booking history, payment records, "
                          "lifetime value calculation, customer segments, export customer data, send bulk emails/SMS, "
                          "track customer preferences, manage customer notes, view review history.",
                "keywords": ["customer", "database", "crm", "contacts", "history", "segment", "export", "manage"],
                "category": "admin_customers",
                "priority": 8
            },
            
            # Newsletter & Marketing
            {
                "content": "Newsletter System: Create email campaigns with templates, segment subscribers, "
                          "schedule send times, track open rates and clicks, A/B testing, automated drip campaigns, "
                          "manage subscriber list, unsubscribe handling, IONOS email integration.",
                "keywords": ["newsletter", "email", "campaign", "marketing", "subscribers", "template", "automation"],
                "category": "admin_newsletter",
                "priority": 7
            },
            
            # Review Management
            {
                "content": "Review Management: Approve/reject customer reviews, moderate blog posts, "
                          "handle escalated issues, respond to feedback, generate review request emails, "
                          "track review stats, issue discount coupons for reviews, integrate with Yelp and Google reviews.",
                "keywords": ["review", "moderation", "approval", "feedback", "blog", "escalation", "moderate"],
                "category": "admin_reviews",
                "priority": 8
            },
            
            # Social Media Integration
            {
                "content": "Social Inbox: Unified inbox for Facebook and Instagram messages, reply to messages, "
                          "convert messages to leads with 1-click, quick reply templates, sentiment indicators, "
                          "response time tracking, unread count badges, message history.",
                "keywords": ["social", "inbox", "facebook", "instagram", "messages", "reply", "sentiment", "unified"],
                "category": "admin_social",
                "priority": 7
            },
            
            # Analytics & Reporting
            {
                "content": "Analytics Dashboard: Revenue trends with charts, booking analytics, "
                          "lead conversion funnel, newsletter performance, customer acquisition cost, "
                          "lead scoring distribution, engagement metrics, source attribution, "
                          "custom date ranges, export reports to CSV/PDF.",
                "keywords": ["analytics", "reports", "metrics", "trends", "charts", "export", "statistics", "data"],
                "category": "admin_analytics",
                "priority": 8
            },
            
            # AI Features
            {
                "content": "AI Assistant: Trained on business knowledge, answers customer questions, "
                          "helps admins with system guidance, provides feature recommendations, "
                          "AI chat for customers on website, AI lead scoring system, "
                          "AI-powered payment matching, sentiment analysis for reviews and messages.",
                "keywords": ["ai", "assistant", "chat", "intelligent", "automation", "learning", "scoring"],
                "category": "admin_ai",
                "priority": 8
            },
            
            # RBAC & Permissions
            {
                "content": "Role-Based Access Control (RBAC): 4 roles - Owner (full access), Manager (operations), "
                          "Admin (most features), Staff (customer-facing only). Permissions: manage users, "
                          "view finances, process refunds, cancel bookings, access sensitive data, "
                          "manage system settings. Admins can be assigned to specific stations/regions.",
                "keywords": ["rbac", "roles", "permissions", "access", "security", "owner", "manager", "admin", "staff"],
                "category": "admin_security",
                "priority": 9
            },
            
            # System Settings
            {
                "content": "System Configuration: Environment variables for API keys (Stripe, Plaid, OpenAI, RingCentral), "
                          "email settings (IONOS SMTP, Gmail), payment options, business hours, service areas, "
                          "rate limiting (20/min public, 100/min admin), CORS domains, Redis cache, PostgreSQL database, "
                          "feature flags for enabling/disabling modules.",
                "keywords": ["settings", "configuration", "environment", "api keys", "setup", "variables", "system"],
                "category": "admin_settings",
                "priority": 9
            }
        ]
        
        for knowledge in business_knowledge:
            chunk_id = str(uuid4())
            self.chunks_cache[chunk_id] = {
                "content": knowledge["content"],
                "metadata": {
                    "category": knowledge["category"],
                    "keywords": knowledge["keywords"],
                    "priority": knowledge.get("priority", 5),
                    "source": "business_config"
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Build keyword index
            for keyword in knowledge["keywords"]:
                if keyword not in self.keywords_index:
                    self.keywords_index[keyword] = []
                self.keywords_index[keyword].append(chunk_id)
        
        logger.info(f"KnowledgeBase: Loaded {len(business_knowledge)} business knowledge chunks (business + admin system)")

    async def enrich_with_database_data(self, db: AsyncSession, query: str) -> List[Dict[str, Any]]:
        """
        Enrich knowledge base with dynamic data from database
        This allows AI to answer questions about actual bookings, reviews, etc.
        """
        dynamic_knowledge = []
        
        try:
            # Check if query is about recent bookings/stats
            if any(word in query.lower() for word in ['recent', 'latest', 'booking', 'reservation', 'event']):
                from models.booking import Booking
                
                # Get recent bookings count
                result = await db.execute(
                    select(func.count(Booking.id))
                    .where(Booking.created_at >= datetime.utcnow().replace(day=1))
                )
                booking_count = result.scalar() or 0
                
                dynamic_knowledge.append({
                    'id': 'db_bookings',
                    'content': f"We have {booking_count} bookings scheduled this month. "
                              f"Our booking system is active and accepting new reservations.",
                    'metadata': {
                        'category': 'booking_stats',
                        'source': 'database',
                        'priority': 10
                    },
                    'score': 0.9
                })
            
            # Check if query is about reviews/feedback
            if any(word in query.lower() for word in ['review', 'rating', 'feedback', 'testimonial', 'customer']):
                from models.review import CustomerReviewBlogPost
                
                # Get approved reviews count
                try:
                    result = await db.execute(
                        select(func.count(CustomerReviewBlogPost.id))
                        .where(CustomerReviewBlogPost.status == 'approved')
                    )
                    review_count = result.scalar() or 0
                    
                    dynamic_knowledge.append({
                        'id': 'db_reviews',
                        'content': f"We have {review_count} verified customer reviews. "
                                  f"Our customers can leave reviews after their events and receive discount coupons.",
                        'metadata': {
                            'category': 'review_stats',
                            'source': 'database',
                            'priority': 8
                        },
                        'score': 0.85
                    })
                except Exception as e:
                    logger.debug(f"Review table not available yet: {e}")
        
        except Exception as e:
            logger.error(f"Error enriching with database data: {e}")
        
        return dynamic_knowledge
    
    async def search_knowledge_base(
        self, query: str, limit: int = 10, min_score: float = 0.3, db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced text search with keyword matching + database integration
        
        Args:
            query: Search query from user
            limit: Maximum results to return
            min_score: Minimum relevance score (0-1)
            db: Optional database session for dynamic data enrichment
        """
        results = []
        
        # Normalize query
        query_words = re.findall(r'\w+', query.lower())
        
        # Score chunks based on keyword and content matching
        for chunk_id, chunk_data in self.chunks_cache.items():
            content = chunk_data.get('content', '').lower()
            keywords = chunk_data.get('metadata', {}).get('keywords', [])
            priority = chunk_data.get('metadata', {}).get('priority', 5)
            
            # Calculate score
            keyword_matches = sum(1 for word in query_words if word in keywords)
            content_matches = sum(1 for word in query_words if word in content)
            
            # Weight: keyword matches > content matches, boost by priority
            base_score = (keyword_matches * 2 + content_matches) / (len(query_words) * 2) if query_words else 0
            priority_boost = priority / 10  # Priority 10 = +1.0 boost
            total_score = min(base_score + (priority_boost * 0.2), 1.0)  # Cap at 1.0
            
            if total_score >= min_score:
                results.append({
                    'id': chunk_id,
                    'content': chunk_data.get('content', ''),
                    'metadata': chunk_data.get('metadata', {}),
                    'score': total_score,
                    'match_type': 'keyword' if keyword_matches > 0 else 'content'
                })
        
        # Enrich with database data if session provided
        if db:
            db_results = await self.enrich_with_database_data(db, query)
            results.extend(db_results)
        
        # Sort by score (priority) and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    async def add_knowledge_chunk(
        self, content: str, metadata: Dict[str, Any] = None
    ) -> str:
        """Add a knowledge chunk to the cache"""
        chunk_id = str(uuid4())
        
        # Extract keywords from content if not provided
        if not metadata or 'keywords' not in metadata:
            keywords = self._extract_keywords(content)
            if not metadata:
                metadata = {}
            metadata['keywords'] = keywords
        
        self.chunks_cache[chunk_id] = {
            'content': content,
            'metadata': metadata,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Update keyword index
        for keyword in metadata.get('keywords', []):
            if keyword not in self.keywords_index:
                self.keywords_index[keyword] = []
            self.keywords_index[keyword].append(chunk_id)
        
        return chunk_id

    def _extract_keywords(self, content: str) -> List[str]:
        """Simple keyword extraction from content"""
        # Remove common words and extract meaningful terms
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = re.findall(r'\w+', content.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        # Return unique keywords, limit to 10
        return list(dict.fromkeys(keywords))[:10]

    async def update_knowledge_chunk(
        self, chunk_id: str, content: str = None, metadata: Dict[str, Any] = None
    ):
        """Update a knowledge chunk"""
        if chunk_id in self.chunks_cache:
            if content is not None:
                self.chunks_cache[chunk_id]['content'] = content
                # Re-extract keywords if content changed
                if metadata is None or 'keywords' not in metadata:
                    keywords = self._extract_keywords(content)
                    self.chunks_cache[chunk_id]['metadata']['keywords'] = keywords
            
            if metadata is not None:
                self.chunks_cache[chunk_id]['metadata'].update(metadata)
            
            self.chunks_cache[chunk_id]['updated_at'] = datetime.utcnow().isoformat()

    async def delete_knowledge_chunk(self, chunk_id: str):
        """Delete a knowledge chunk"""
        if chunk_id in self.chunks_cache:
            # Remove from keyword index
            keywords = self.chunks_cache[chunk_id].get('metadata', {}).get('keywords', [])
            for keyword in keywords:
                if keyword in self.keywords_index:
                    self.keywords_index[keyword] = [cid for cid in self.keywords_index[keyword] if cid != chunk_id]
                    if not self.keywords_index[keyword]:
                        del self.keywords_index[keyword]
            
            del self.chunks_cache[chunk_id]

    async def get_chunk_count(self) -> int:
        """Get total number of chunks"""
        return len(self.chunks_cache)

    async def clear_knowledge_base(self):
        """Clear all knowledge base data"""
        self.chunks_cache.clear()
        self.keywords_index.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_chunks": len(self.chunks_cache),
            "total_keywords": len(self.keywords_index),
            "has_index": True,
            "encoder_model": "production_keyword_matching",
            "embedding_dim": 0,
            "service_type": "production_integrated",
            "database_enrichment": True,
            "vps_compatible": True,
            "data_sources": ["business_config", "database_dynamic", "settings"]
        }


# Global service instance
kb_service = ProductionKnowledgeBaseService()