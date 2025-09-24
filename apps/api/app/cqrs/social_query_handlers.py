"""Social media CQRS query handlers."""

import logging
from typing import Any

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.cqrs.base import QueryHandler
from app.cqrs.social_queries import (
    GetReviewsBoardQuery,
    GetSocialInboxQuery,
    GetThreadDetailQuery,
    GetUnreadCountsQuery,
)
from app.models.core import Customer
from app.models.social import Review, SocialAccount, SocialMessage, SocialThread

logger = logging.getLogger(__name__)


class GetSocialInboxHandler(QueryHandler[GetSocialInboxQuery]):
    """Handler for getting social media inbox."""

    async def handle(self, query: GetSocialInboxQuery, session: AsyncSession) -> dict[str, Any]:
        try:
            # Build base query for threads with latest message
            base_stmt = select(SocialThread).options(
                joinedload(SocialThread.account),
                joinedload(SocialThread.customer_identity),
                selectinload(SocialThread.messages).options(
                    joinedload(SocialMessage.sender_identity)
                )
            )

            # Apply filters
            filters = []

            if query.platforms:
                filters.append(
                    SocialThread.account.has(SocialAccount.platform.in_(query.platforms))
                )

            if query.statuses:
                filters.append(SocialThread.status.in_(query.statuses))

            if query.assigned_to:
                filters.append(SocialThread.assigned_to == query.assigned_to)

            if query.date_from:
                filters.append(SocialThread.created_at >= query.date_from)

            if query.date_to:
                filters.append(SocialThread.created_at <= query.date_to)

            if query.search:
                # Search in thread metadata or recent messages
                search_filter = or_(
                    SocialThread.metadata['customer_name'].astext.ilike(f"%{query.search}%"),
                    SocialThread.messages.any(SocialMessage.body.ilike(f"%{query.search}%"))
                )
                filters.append(search_filter)

            if query.has_unread is not None:
                if query.has_unread:
                    filters.append(SocialThread.unread_count > 0)
                else:
                    filters.append(SocialThread.unread_count == 0)

            if query.priority_min:
                filters.append(SocialThread.priority >= query.priority_min)

            if query.tags:
                for tag in query.tags:
                    filters.append(
                        SocialThread.metadata['tags'].astext.contains(f'"{tag}"')
                    )

            if filters:
                base_stmt = base_stmt.where(and_(*filters))

            # Apply sorting
            if query.sort_by == "updated_at":
                sort_column = SocialThread.updated_at
            elif query.sort_by == "created_at":
                sort_column = SocialThread.created_at
            elif query.sort_by == "priority":
                sort_column = SocialThread.priority
            elif query.sort_by == "last_message_at":
                sort_column = SocialThread.last_message_at
            else:
                sort_column = SocialThread.updated_at

            if query.sort_order == "desc":
                base_stmt = base_stmt.order_by(desc(sort_column))
            else:
                base_stmt = base_stmt.order_by(asc(sort_column))

            # Get total count
            count_stmt = select(func.count()).select_from(
                base_stmt.subquery()
            )
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()

            # Apply pagination
            offset = (query.page - 1) * query.page_size
            paginated_stmt = base_stmt.offset(offset).limit(query.page_size)

            result = await session.execute(paginated_stmt)
            threads = result.unique().scalars().all()

            # Format response
            thread_data = []
            for thread in threads:
                # Get latest message
                latest_message = None
                if thread.messages:
                    latest_message = max(thread.messages, key=lambda m: m.created_at)

                thread_info = {
                    "id": thread.id,
                    "platform": thread.account.platform,
                    "status": thread.status,
                    "priority": thread.priority,
                    "customer_name": thread.metadata.get("customer_name"),
                    "handle": thread.customer_identity.handle if thread.customer_identity else None,
                    "unread_count": thread.unread_count,
                    "created_at": thread.created_at,
                    "updated_at": thread.updated_at,
                    "last_message_at": thread.last_message_at,
                    "assigned_to": thread.assigned_to,
                    "tags": thread.metadata.get("tags", []),
                    "latest_message": {
                        "id": latest_message.id,
                        "body": latest_message.body[:100] + ("..." if len(latest_message.body) > 100 else ""),
                        "kind": latest_message.kind,
                        "direction": latest_message.direction,
                        "created_at": latest_message.created_at,
                        "sender_name": latest_message.sender_name
                    } if latest_message else None,
                    "customer_profile": {
                        "id": thread.customer_identity.customer_id,
                        "name": thread.metadata.get("customer_name"),
                        "avatar": thread.metadata.get("customer_avatar")
                    } if thread.customer_identity and thread.customer_identity.customer_id else None
                }

                thread_data.append(thread_info)

            return {
                "threads": thread_data,
                "pagination": {
                    "page": query.page,
                    "page_size": query.page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + query.page_size - 1) // query.page_size
                },
                "filters_applied": {
                    "platforms": query.platforms,
                    "statuses": query.statuses,
                    "search": query.search,
                    "has_unread": query.has_unread,
                    "date_range": [query.date_from, query.date_to] if query.date_from or query.date_to else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting social inbox: {e}")
            raise


class GetReviewsBoardHandler(QueryHandler[GetReviewsBoardQuery]):
    """Handler for getting reviews dashboard."""

    async def handle(self, query: GetReviewsBoardQuery, session: AsyncSession) -> dict[str, Any]:
        try:
            # Build base query for reviews
            base_stmt = select(Review).options(
                joinedload(Review.account),
                joinedload(Review.customer_identity)
            )

            # Apply filters
            filters = []

            if query.platforms:
                filters.append(
                    Review.account.has(SocialAccount.platform.in_(query.platforms))
                )

            if query.statuses:
                filters.append(Review.status.in_(query.statuses))

            if query.rating_min is not None:
                filters.append(Review.rating >= query.rating_min)

            if query.rating_max is not None:
                filters.append(Review.rating <= query.rating_max)

            if query.date_from:
                filters.append(Review.created_at >= query.date_from)

            if query.date_to:
                filters.append(Review.created_at <= query.date_to)

            if query.search:
                search_filter = or_(
                    Review.body.ilike(f"%{query.search}%"),
                    Review.metadata['customer_name'].astext.ilike(f"%{query.search}%")
                )
                filters.append(search_filter)

            if query.priority_min:
                filters.append(Review.priority_level >= query.priority_min)

            if query.assigned_to:
                filters.append(Review.assigned_to == query.assigned_to)

            if query.escalated_only:
                filters.append(Review.escalated_at.isnot(None))

            if filters:
                base_stmt = base_stmt.where(and_(*filters))

            # Apply sorting
            if query.sort_by == "created_at":
                sort_column = Review.created_at
            elif query.sort_by == "rating":
                sort_column = Review.rating
            elif query.sort_by == "priority_level":
                sort_column = Review.priority_level
            elif query.sort_by == "updated_at":
                sort_column = Review.updated_at
            else:
                sort_column = Review.created_at

            if query.sort_order == "desc":
                base_stmt = base_stmt.order_by(desc(sort_column))
            else:
                base_stmt = base_stmt.order_by(asc(sort_column))

            # Get total count
            count_stmt = select(func.count()).select_from(
                base_stmt.subquery()
            )
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()

            # Apply pagination
            offset = (query.page - 1) * query.page_size
            paginated_stmt = base_stmt.offset(offset).limit(query.page_size)

            result = await session.execute(paginated_stmt)
            reviews = result.unique().scalars().all()

            # Format response
            review_data = []
            for review in reviews:
                review_info = {
                    "id": review.id,
                    "platform": review.account.platform,
                    "rating": review.rating,
                    "status": review.status,
                    "priority_level": review.priority_level,
                    "body": review.body,
                    "customer_name": review.metadata.get("customer_name"),
                    "customer_handle": review.customer_identity.handle if review.customer_identity else None,
                    "created_at": review.created_at,
                    "updated_at": review.updated_at,
                    "acknowledged_at": review.acknowledged_at,
                    "acknowledged_by": review.acknowledged_by,
                    "escalated_at": review.escalated_at,
                    "assigned_to": review.assigned_to,
                    "business_reply": review.metadata.get("business_reply"),
                    "reply_posted_at": review.metadata.get("reply_posted_at"),
                    "sentiment_score": review.metadata.get("sentiment_score"),
                    "key_topics": review.metadata.get("key_topics", [])
                }

                review_data.append(review_info)

            # Get summary statistics
            stats_stmt = select(
                func.count(Review.id).label("total_reviews"),
                func.avg(Review.rating).label("avg_rating"),
                func.count().filter(Review.rating <= 2).label("negative_reviews"),
                func.count().filter(Review.rating >= 4).label("positive_reviews"),
                func.count().filter(Review.status == "new").label("new_reviews"),
                func.count().filter(Review.escalated_at.isnot(None)).label("escalated_reviews")
            ).where(and_(*filters)) if filters else select(
                func.count(Review.id).label("total_reviews"),
                func.avg(Review.rating).label("avg_rating"),
                func.count().filter(Review.rating <= 2).label("negative_reviews"),
                func.count().filter(Review.rating >= 4).label("positive_reviews"),
                func.count().filter(Review.status == "new").label("new_reviews"),
                func.count().filter(Review.escalated_at.isnot(None)).label("escalated_reviews")
            )

            stats_result = await session.execute(stats_stmt)
            stats = stats_result.one()

            return {
                "reviews": review_data,
                "pagination": {
                    "page": query.page,
                    "page_size": query.page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + query.page_size - 1) // query.page_size
                },
                "summary": {
                    "total_reviews": stats.total_reviews,
                    "average_rating": round(float(stats.avg_rating), 2) if stats.avg_rating else 0,
                    "negative_reviews": stats.negative_reviews,
                    "positive_reviews": stats.positive_reviews,
                    "new_reviews": stats.new_reviews,
                    "escalated_reviews": stats.escalated_reviews
                },
                "filters_applied": {
                    "platforms": query.platforms,
                    "statuses": query.statuses,
                    "rating_range": [query.rating_min, query.rating_max],
                    "search": query.search,
                    "escalated_only": query.escalated_only
                }
            }

        except Exception as e:
            logger.error(f"Error getting reviews board: {e}")
            raise


class GetThreadDetailHandler(QueryHandler[GetThreadDetailQuery]):
    """Handler for getting detailed thread information."""

    async def handle(self, query: GetThreadDetailQuery, session: AsyncSession) -> dict[str, Any]:
        try:
            # Get thread with related data
            thread_stmt = select(SocialThread).options(
                joinedload(SocialThread.account),
                joinedload(SocialThread.customer_identity),
                selectinload(SocialThread.messages).options(
                    joinedload(SocialMessage.sender_identity)
                ) if query.include_messages else lambda: None
            ).where(SocialThread.id == query.thread_id)

            result = await session.execute(thread_stmt)
            thread = result.unique().scalar_one_or_none()

            if not thread:
                raise ValueError(f"Thread {query.thread_id} not found")

            # Build thread detail response
            thread_detail = {
                "id": thread.id,
                "platform": thread.account.platform,
                "status": thread.status,
                "priority": thread.priority,
                "unread_count": thread.unread_count,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,
                "last_message_at": thread.last_message_at,
                "assigned_to": thread.assigned_to,
                "metadata": thread.metadata,
                "account": {
                    "id": thread.account.id,
                    "platform": thread.account.platform,
                    "page_name": thread.account.page_name,
                    "handle": thread.account.handle
                }
            }

            # Add messages if requested
            if query.include_messages and thread.messages:
                messages = sorted(thread.messages, key=lambda m: m.created_at)
                thread_detail["messages"] = [
                    {
                        "id": msg.id,
                        "kind": msg.kind,
                        "direction": msg.direction,
                        "body": msg.body,
                        "sender_handle": msg.sender_handle,
                        "sender_name": msg.sender_name,
                        "created_at": msg.created_at,
                        "sent_at": msg.sent_at,
                        "platform_message_id": msg.platform_message_id,
                        "metadata": msg.metadata,
                        "sender_profile": {
                            "id": msg.sender_identity.id,
                            "handle": msg.sender_identity.handle,
                            "profile_data": msg.sender_identity.profile_data
                        } if msg.sender_identity else None
                    }
                    for msg in messages
                ]

            # Add customer profile if requested
            if query.include_customer_profile and thread.customer_identity:
                if thread.customer_identity.customer_id:
                    customer_stmt = select(Customer).where(
                        Customer.id == thread.customer_identity.customer_id
                    )
                    customer_result = await session.execute(customer_stmt)
                    customer = customer_result.scalar_one_or_none()

                    if customer:
                        thread_detail["customer_profile"] = {
                            "id": customer.id,
                            "first_name": customer.first_name,
                            "last_name": customer.last_name,
                            "email": customer.email,
                            "phone": customer.phone,
                            "created_at": customer.created_at,
                            "metadata": customer.metadata,
                            "social_identity": {
                                "id": thread.customer_identity.id,
                                "handle": thread.customer_identity.handle,
                                "platform": thread.customer_identity.platform,
                                "profile_data": thread.customer_identity.profile_data
                            }
                        }
                else:
                    # Customer identity not linked to customer yet
                    thread_detail["customer_profile"] = {
                        "social_identity": {
                            "id": thread.customer_identity.id,
                            "handle": thread.customer_identity.handle,
                            "platform": thread.customer_identity.platform,
                            "profile_data": thread.customer_identity.profile_data
                        },
                        "linked": False
                    }

            # Add related threads if requested
            if query.include_related_threads and thread.customer_identity:
                related_stmt = select(SocialThread).options(
                    joinedload(SocialThread.account)
                ).where(
                    and_(
                        SocialThread.customer_identity_id == thread.customer_identity.id,
                        SocialThread.id != thread.id
                    )
                ).order_by(desc(SocialThread.updated_at)).limit(5)

                related_result = await session.execute(related_stmt)
                related_threads = related_result.unique().scalars().all()

                thread_detail["related_threads"] = [
                    {
                        "id": rt.id,
                        "platform": rt.account.platform,
                        "status": rt.status,
                        "priority": rt.priority,
                        "created_at": rt.created_at,
                        "last_message_at": rt.last_message_at
                    }
                    for rt in related_threads
                ]

            return thread_detail

        except Exception as e:
            logger.error(f"Error getting thread detail: {e}")
            raise


class GetUnreadCountsHandler(QueryHandler[GetUnreadCountsQuery]):
    """Handler for getting unread message counts."""

    async def handle(self, query: GetUnreadCountsQuery, session: AsyncSession) -> dict[str, Any]:
        try:
            # Build base query
            base_stmt = select(
                SocialAccount.platform,
                SocialThread.status,
                SocialThread.priority,
                func.count(SocialThread.id).label("thread_count"),
                func.sum(SocialThread.unread_count).label("unread_count")
            ).select_from(
                SocialThread
            ).join(
                SocialAccount, SocialThread.account_id == SocialAccount.id
            )

            # Apply filters
            filters = []

            if query.platforms:
                filters.append(SocialAccount.platform.in_(query.platforms))

            if query.assigned_to:
                filters.append(SocialThread.assigned_to == query.assigned_to)

            # Only include threads with unread messages
            filters.append(SocialThread.unread_count > 0)

            if filters:
                base_stmt = base_stmt.where(and_(*filters))

            # Group by the requested field
            if query.group_by == "platform":
                base_stmt = base_stmt.group_by(SocialAccount.platform)
                result = await session.execute(base_stmt)

                counts = {}
                for row in result:
                    counts[row.platform] = {
                        "thread_count": row.thread_count,
                        "unread_count": row.unread_count or 0
                    }

            elif query.group_by == "status":
                base_stmt = base_stmt.group_by(SocialThread.status)
                result = await session.execute(base_stmt)

                counts = {}
                for row in result:
                    counts[row.status] = {
                        "thread_count": row.thread_count,
                        "unread_count": row.unread_count or 0
                    }

            elif query.group_by == "priority":
                base_stmt = base_stmt.group_by(SocialThread.priority)
                result = await session.execute(base_stmt)

                counts = {}
                for row in result:
                    counts[f"priority_{row.priority}"] = {
                        "thread_count": row.thread_count,
                        "unread_count": row.unread_count or 0
                    }
            else:
                # Default to platform grouping
                base_stmt = base_stmt.group_by(SocialAccount.platform)
                result = await session.execute(base_stmt)

                counts = {}
                for row in result:
                    counts[row.platform] = {
                        "thread_count": row.thread_count,
                        "unread_count": row.unread_count or 0
                    }

            # Get total counts
            total_stmt = select(
                func.count(SocialThread.id).label("total_threads"),
                func.sum(SocialThread.unread_count).label("total_unread")
            ).select_from(SocialThread)

            if filters[:-1]:  # Exclude the unread filter for total
                total_stmt = total_stmt.where(and_(*filters[:-1]))

            total_result = await session.execute(total_stmt)
            totals = total_result.one()

            return {
                "counts": counts,
                "totals": {
                    "total_threads": totals.total_threads or 0,
                    "total_unread": totals.total_unread or 0
                },
                "group_by": query.group_by,
                "filters_applied": {
                    "platforms": query.platforms,
                    "assigned_to": query.assigned_to
                }
            }

        except Exception as e:
            logger.error(f"Error getting unread counts: {e}")
            raise
