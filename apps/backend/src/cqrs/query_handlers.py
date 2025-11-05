"""
Query handlers for CRM read operations using materialized views.
"""

from datetime import datetime
from typing import Any

from api.app.cqrs.base import QueryHandler, QueryResult
from api.app.cqrs.crm_operations import *
from api.app.utils.encryption import FieldEncryption
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class GetBookingQueryHandler(QueryHandler):
    """Get detailed booking information."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.encryption = FieldEncryption()

    async def handle(self, query: GetBookingQuery) -> QueryResult:
        """Get booking details with related data."""
        try:
            # Use the booking_detail materialized view for optimized reads
            stmt = text(
                """
                SELECT
                    bd.*,
                    CASE WHEN :include_payments THEN
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'payment_id', p.id,
                                    'amount_cents', p.amount_cents,
                                    'payment_method', p.payment_method,
                                    'payment_reference', p.payment_reference,
                                    'processed_at', p.processed_at,
                                    'processed_by', p.processed_by,
                                    'status', p.status
                                ) ORDER BY p.processed_at
                            ) FILTER (WHERE p.id IS NOT NULL),
                            '[]'::json
                        )
                    END as payments,
                    CASE WHEN :include_messages THEN
                        COALESCE(
                            json_agg(
                                DISTINCT json_build_object(
                                    'thread_id', mt.id,
                                    'phone_number', mt.phone_number_encrypted,
                                    'last_message_at', mt.last_message_at,
                                    'has_unread', mt.has_unread,
                                    'status', mt.status
                                ) ORDER BY mt.created_at
                            ) FILTER (WHERE mt.id IS NOT NULL),
                            '[]'::json
                        )
                    END as message_threads
                FROM read.booking_detail bd
                LEFT JOIN core.payments p ON p.booking_id = bd.booking_id AND :include_payments
                LEFT JOIN core.message_threads mt ON mt.booking_id = bd.booking_id AND :include_messages
                WHERE bd.booking_id = :booking_id
                GROUP BY bd.booking_id, bd.customer_id, bd.customer_email_encrypted,
                         bd.customer_name_encrypted, bd.customer_phone_encrypted,
                         bd.date, bd.slot, bd.total_guests, bd.price_per_person_cents,
                         bd.total_due_cents, bd.deposit_due_cents, bd.balance_due_cents,
                         bd.status, bd.payment_status, bd.special_requests_encrypted,
                         bd.source, bd.ai_conversation_id, bd.created_at, bd.updated_at
            """
            )

            result = await self.session.execute(
                stmt,
                {
                    "booking_id": str(query.booking_id),
                    "include_payments": query.include_payments,
                    "include_messages": query.include_messages,
                },
            )

            row = result.fetchone()
            if not row:
                return QueryResult(success=False, error=f"Booking {query.booking_id} not found")

            # Decrypt sensitive fields
            booking_data = dict(row._mapping)
            booking_data["customer_email"] = self.encryption.decrypt(
                booking_data["customer_email_encrypted"]
            )
            booking_data["customer_name"] = self.encryption.decrypt(
                booking_data["customer_name_encrypted"]
            )
            booking_data["customer_phone"] = self.encryption.decrypt(
                booking_data["customer_phone_encrypted"]
            )

            # Decrypt special requests if present
            if booking_data.get("special_requests_encrypted"):
                booking_data["special_requests"] = self.encryption.decrypt(
                    booking_data["special_requests_encrypted"]
                )

            # Remove encrypted fields from response
            for field in [
                "customer_email_encrypted",
                "customer_name_encrypted",
                "customer_phone_encrypted",
                "special_requests_encrypted",
            ]:
                booking_data.pop(field, None)

            # Decrypt phone numbers in message threads if included
            if query.include_messages and booking_data.get("message_threads"):
                for thread in booking_data["message_threads"]:
                    if thread.get("phone_number"):
                        thread["phone_number"] = self.encryption.decrypt(thread["phone_number"])

            return QueryResult(success=True, data=booking_data)

        except Exception as e:
            return QueryResult(success=False, error=str(e))


class GetBookingsQueryHandler(QueryHandler):
    """Get filtered and paginated bookings list."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.encryption = FieldEncryption()

    async def handle(self, query: GetBookingsQuery) -> QueryResult:
        """Get bookings with filters and pagination."""
        try:
            # Build dynamic query conditions
            conditions = []
            params = {"limit": query.page_size, "offset": (query.page - 1) * query.page_size}

            if query.customer_email:
                # We need to encrypt the email to search
                encrypted_email = self.encryption.encrypt(query.customer_email)
                conditions.append("bd.customer_email_encrypted = :customer_email")
                params["customer_email"] = encrypted_email

            if query.customer_phone:
                encrypted_phone = self.encryption.encrypt(query.customer_phone)
                conditions.append("bd.customer_phone_encrypted = :customer_phone")
                params["customer_phone"] = encrypted_phone

            if query.date_from:
                conditions.append("bd.date >= :date_from")
                params["date_from"] = query.date_from

            if query.date_to:
                conditions.append("bd.date <= :date_to")
                params["date_to"] = query.date_to

            if query.status:
                conditions.append("bd.status = :status")
                params["status"] = query.status

            if query.source:
                conditions.append("bd.source = :source")
                params["source"] = query.source

            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

            # Build ORDER BY clause
            sort_direction = "DESC" if query.sort_order == "desc" else "ASC"
            order_by = f"ORDER BY bd.{query.sort_by} {sort_direction}"

            # Main query
            stmt = text(
                f"""
                SELECT
                    bd.booking_id,
                    bd.customer_email_encrypted,
                    bd.customer_name_encrypted,
                    bd.customer_phone_encrypted,
                    bd.date,
                    bd.slot,
                    bd.total_guests,
                    bd.total_due_cents,
                    bd.balance_due_cents,
                    bd.status,
                    bd.payment_status,
                    bd.source,
                    bd.created_at,
                    bd.updated_at
                FROM read.booking_detail bd
                {where_clause}
                {order_by}
                LIMIT :limit OFFSET :offset
            """
            )

            # Count query for pagination
            count_stmt = text(
                f"""
                SELECT COUNT(*) as total
                FROM read.booking_detail bd
                {where_clause}
            """
            )

            # Execute both queries
            result = await self.session.execute(stmt, params)
            count_result = await self.session.execute(count_stmt, params)

            bookings = []
            for row in result.fetchall():
                booking_data = dict(row._mapping)

                # Decrypt sensitive fields
                booking_data["customer_email"] = self.encryption.decrypt(
                    booking_data["customer_email_encrypted"]
                )
                booking_data["customer_name"] = self.encryption.decrypt(
                    booking_data["customer_name_encrypted"]
                )
                booking_data["customer_phone"] = self.encryption.decrypt(
                    booking_data["customer_phone_encrypted"]
                )

                # Remove encrypted fields
                for field in [
                    "customer_email_encrypted",
                    "customer_name_encrypted",
                    "customer_phone_encrypted",
                ]:
                    booking_data.pop(field)

                bookings.append(booking_data)

            total_count = count_result.scalar()

            return QueryResult(success=True, data=bookings, total_count=total_count)

        except Exception as e:
            return QueryResult(success=False, error=str(e))


class GetCustomer360QueryHandler(QueryHandler):
    """Get comprehensive customer view."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.encryption = FieldEncryption()

    async def handle(self, query: GetCustomer360Query) -> QueryResult:
        """Get 360-degree customer view."""
        try:
            # Build WHERE condition based on provided identifier
            if query.customer_id:
                where_condition = "c360.customer_id = :identifier"
                params = {"identifier": str(query.customer_id)}
            elif query.customer_email:
                where_condition = "c360.customer_email_encrypted = :identifier"
                params = {"identifier": self.encryption.encrypt(query.customer_email)}
            elif query.customer_phone:
                where_condition = "c360.customer_phone_encrypted = :identifier"
                params = {"identifier": self.encryption.encrypt(query.customer_phone)}
            else:
                return QueryResult(
                    success=False,
                    error="Must provide customer_id, customer_email, or customer_phone",
                )

            # Use customer_360 materialized view
            stmt = text(
                f"""
                SELECT
                    c360.*,
                    CASE WHEN :include_bookings THEN
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'booking_id', b.id,
                                    'date', b.date,
                                    'slot', b.slot,
                                    'total_guests', b.total_guests,
                                    'total_due_cents', b.total_due_cents,
                                    'balance_due_cents', b.balance_due_cents,
                                    'status', b.status,
                                    'payment_status', b.payment_status,
                                    'source', b.source,
                                    'created_at', b.created_at
                                ) ORDER BY b.date DESC
                            ) FILTER (WHERE b.id IS NOT NULL),
                            '[]'::json
                        )
                    END as bookings,
                    CASE WHEN :include_payments THEN
                        COALESCE(
                            json_agg(
                                DISTINCT json_build_object(
                                    'payment_id', p.id,
                                    'booking_id', p.booking_id,
                                    'amount_cents', p.amount_cents,
                                    'payment_method', p.payment_method,
                                    'processed_at', p.processed_at,
                                    'status', p.status
                                ) ORDER BY p.processed_at DESC
                            ) FILTER (WHERE p.id IS NOT NULL),
                            '[]'::json
                        )
                    END as payments,
                    CASE WHEN :include_messages THEN
                        COALESCE(
                            json_agg(
                                DISTINCT json_build_object(
                                    'thread_id', mt.id,
                                    'phone_number', mt.phone_number_encrypted,
                                    'last_message_at', mt.last_message_at,
                                    'has_unread', mt.has_unread,
                                    'status', mt.status
                                ) ORDER BY mt.created_at DESC
                            ) FILTER (WHERE mt.id IS NOT NULL),
                            '[]'::json
                        )
                    END as message_threads
                FROM read.customer_360 c360
                LEFT JOIN core.bookings b ON b.customer_id = c360.customer_id AND :include_bookings
                LEFT JOIN core.payments p ON p.booking_id = b.id AND :include_payments
                LEFT JOIN core.message_threads mt ON mt.customer_id = c360.customer_id AND :include_messages
                WHERE {where_condition}
                GROUP BY c360.customer_id, c360.customer_email_encrypted, c360.customer_name_encrypted,
                         c360.customer_phone_encrypted, c360.source, c360.first_booking_at,
                         c360.last_booking_at, c360.total_bookings, c360.total_spent_cents,
                         c360.created_at, c360.updated_at
            """
            )

            params.update(
                {
                    "include_bookings": query.include_bookings,
                    "include_payments": query.include_payments,
                    "include_messages": query.include_messages,
                }
            )

            result = await self.session.execute(stmt, params)
            row = result.fetchone()

            if not row:
                return QueryResult(success=False, error="Customer not found")

            # Decrypt and format response
            customer_data = dict(row._mapping)

            # Decrypt PII fields
            customer_data["customer_email"] = self.encryption.decrypt(
                customer_data["customer_email_encrypted"]
            )
            customer_data["customer_name"] = self.encryption.decrypt(
                customer_data["customer_name_encrypted"]
            )
            customer_data["customer_phone"] = self.encryption.decrypt(
                customer_data["customer_phone_encrypted"]
            )

            # Remove encrypted fields
            for field in [
                "customer_email_encrypted",
                "customer_name_encrypted",
                "customer_phone_encrypted",
            ]:
                customer_data.pop(field, None)

            # Decrypt phone numbers in message threads
            if query.include_messages and customer_data.get("message_threads"):
                for thread in customer_data["message_threads"]:
                    if thread.get("phone_number"):
                        thread["phone_number"] = self.encryption.decrypt(thread["phone_number"])

            return QueryResult(success=True, data=customer_data)

        except Exception as e:
            return QueryResult(success=False, error=str(e))


class GetMessageThreadQueryHandler(QueryHandler):
    """Get message thread with history."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.encryption = FieldEncryption()

    async def handle(self, query: GetMessageThreadQuery) -> QueryResult:
        """Get message thread with decrypted messages."""
        try:
            # Get thread details with messages using raw SQL for better performance
            stmt = text(
                """
                SELECT
                    mt.id as thread_id,
                    mt.phone_number_encrypted,
                    mt.status,
                    mt.has_unread,
                    mt.last_message_at,
                    mt.booking_id,
                    mt.subject,
                    mt.created_at,
                    CASE WHEN :include_customer_details AND c.id IS NOT NULL THEN
                        json_build_object(
                            'customer_id', c.id,
                            'name', c.name_encrypted,
                            'email', c.email_encrypted,
                            'total_bookings', c.total_bookings,
                            'total_spent_cents', c.total_spent_cents
                        )
                    END as customer,
                    CASE WHEN :include_booking_context AND b.id IS NOT NULL THEN
                        json_build_object(
                            'booking_id', b.id,
                            'date', b.date,
                            'slot', b.slot,
                            'total_guests', b.total_guests,
                            'status', b.status
                        )
                    END as booking,
                    json_agg(
                        json_build_object(
                            'message_id', m.id,
                            'content_encrypted', m.content_encrypted,
                            'direction', m.direction,
                            'status', m.status,
                            'sent_at', m.sent_at,
                            'sent_by', m.sent_by,
                            'external_message_id', m.external_message_id,
                            'source', m.source
                        ) ORDER BY m.sent_at DESC
                    ) as messages
                FROM core.message_threads mt
                LEFT JOIN core.customers c ON c.id = mt.customer_id
                LEFT JOIN core.bookings b ON b.id = mt.booking_id
                LEFT JOIN (
                    SELECT * FROM core.messages
                    WHERE thread_id = :thread_id
                    ORDER BY sent_at DESC
                    LIMIT :limit
                ) m ON m.thread_id = mt.id
                WHERE mt.id = :thread_id
                GROUP BY mt.id, mt.phone_number_encrypted, mt.status, mt.has_unread,
                         mt.last_message_at, mt.booking_id, mt.subject, mt.created_at,
                         c.id, c.name_encrypted, c.email_encrypted, c.total_bookings, c.total_spent_cents,
                         b.id, b.date, b.slot, b.total_guests, b.status
            """
            )

            result = await self.session.execute(
                stmt,
                {
                    "thread_id": str(query.thread_id),
                    "include_customer_details": query.include_customer_details,
                    "include_booking_context": query.include_booking_context,
                    "limit": query.limit,
                },
            )

            row = result.fetchone()
            if not row:
                return QueryResult(
                    success=False, error=f"Message thread {query.thread_id} not found"
                )

            # Process and decrypt response
            thread_data = dict(row._mapping)

            # Decrypt phone number
            thread_data["phone_number"] = self.encryption.decrypt(
                thread_data["phone_number_encrypted"]
            )
            thread_data.pop("phone_number_encrypted")

            # Decrypt customer details if included
            if query.include_customer_details and thread_data.get("customer"):
                customer = thread_data["customer"]
                if customer.get("name"):
                    customer["name"] = self.encryption.decrypt(customer["name"])
                if customer.get("email"):
                    customer["email"] = self.encryption.decrypt(customer["email"])

            # Decrypt message contents
            if thread_data.get("messages"):
                for message in thread_data["messages"]:
                    if message.get("content_encrypted"):
                        message["content"] = self.encryption.decrypt(message["content_encrypted"])
                        message.pop("content_encrypted")

            return QueryResult(success=True, data=thread_data)

        except Exception as e:
            return QueryResult(success=False, error=str(e))


class GetAvailabilitySlotsQueryHandler(QueryHandler):
    """Get available time slots for booking."""

    async def handle(self, query: GetAvailabilitySlotsQuery) -> QueryResult:
        """Get available slots using schedule_board view."""
        try:
            # Use the schedule_board materialized view for optimized availability
            stmt = text(
                """
                SELECT
                    slot,
                    max_capacity,
                    current_bookings,
                    available_capacity,
                    CASE
                        WHEN available_capacity >= :party_size THEN true
                        ELSE false
                    END as is_available,
                    json_agg(
                        json_build_object(
                            'booking_id', booking_id,
                            'customer_name_encrypted', customer_name_encrypted,
                            'total_guests', total_guests,
                            'status', status
                        ) ORDER BY created_at
                    ) FILTER (WHERE booking_id IS NOT NULL) as current_reservations
                FROM read.schedule_board
                WHERE date_slot = :date
                GROUP BY slot, max_capacity, current_bookings, available_capacity
                ORDER BY slot
            """
            )

            result = await self.session.execute(
                stmt, {"date": query.date, "party_size": query.party_size}
            )

            slots = []
            for row in result.fetchall():
                slot_data = dict(row._mapping)

                # Decrypt customer names in reservations (for staff view)
                if slot_data.get("current_reservations"):
                    for reservation in slot_data["current_reservations"]:
                        if reservation.get("customer_name_encrypted"):
                            reservation["customer_name"] = self.encryption.decrypt(
                                reservation["customer_name_encrypted"]
                            )
                            reservation.pop("customer_name_encrypted")

                slots.append(slot_data)

            return QueryResult(
                success=True,
                data={"date": query.date, "party_size": query.party_size, "slots": slots},
            )

        except Exception as e:
            return QueryResult(success=False, error=str(e))


class GetDashboardStatsQueryHandler(QueryHandler):
    """Get dashboard statistics."""

    async def handle(self, query: GetDashboardStatsQuery) -> QueryResult:
        """Get dashboard stats with date filtering."""
        try:
            # Default to current month if no dates provided
            if not query.date_from or not query.date_to:
                from datetime import date

                today = date.today()
                if not query.date_from:
                    query.date_from = today.replace(day=1)
                if not query.date_to:
                    query.date_to = today

            stats = {}

            if query.include_bookings:
                booking_stats = await self._get_booking_stats(query.date_from, query.date_to)
                stats.update(booking_stats)

            if query.include_revenue:
                revenue_stats = await self._get_revenue_stats(query.date_from, query.date_to)
                stats.update(revenue_stats)

            if query.include_messages:
                message_stats = await self._get_message_stats(query.date_from, query.date_to)
                stats.update(message_stats)

            return QueryResult(
                success=True,
                data={"period": {"from": query.date_from, "to": query.date_to}, "stats": stats},
            )

        except Exception as e:
            return QueryResult(success=False, error=str(e))

    async def _get_booking_stats(self, date_from, date_to) -> dict[str, Any]:
        """Get booking statistics."""
        stmt = text(
            """
            SELECT
                COUNT(*) as total_bookings,
                COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed_bookings,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_bookings,
                SUM(total_guests) as total_guests,
                AVG(total_guests::decimal) as avg_party_size,
                COUNT(DISTINCT customer_id) as unique_customers,
                COUNT(*) FILTER (WHERE source = 'ai') as ai_bookings,
                COUNT(*) FILTER (WHERE source = 'website') as website_bookings
            FROM core.bookings
            WHERE date BETWEEN :date_from AND :date_to
        """
        )

        result = await self.session.execute(stmt, {"date_from": date_from, "date_to": date_to})

        row = result.fetchone()
        return dict(row._mapping) if row else {}

    async def _get_revenue_stats(self, date_from, date_to) -> dict[str, Any]:
        """Get revenue statistics."""
        stmt = text(
            """
            SELECT
                COALESCE(SUM(b.total_due_cents), 0) as total_revenue_cents,
                COALESCE(SUM(p.amount_cents), 0) as collected_revenue_cents,
                COALESCE(SUM(b.balance_due_cents), 0) as outstanding_revenue_cents,
                COUNT(p.id) as total_payments,
                AVG(b.total_due_cents::decimal) as avg_booking_value_cents
            FROM core.bookings b
            LEFT JOIN core.payments p ON p.booking_id = b.id
            WHERE b.date BETWEEN :date_from AND :date_to
        """
        )

        result = await self.session.execute(stmt, {"date_from": date_from, "date_to": date_to})

        row = result.fetchone()
        return dict(row._mapping) if row else {}

    async def _get_message_stats(self, date_from, date_to) -> dict[str, Any]:
        """Get message statistics."""
        stmt = text(
            """
            SELECT
                COUNT(DISTINCT mt.id) as active_threads,
                COUNT(*) FILTER (WHERE m.direction = 'inbound') as inbound_messages,
                COUNT(*) FILTER (WHERE m.direction = 'outbound') as outbound_messages,
                COUNT(*) FILTER (WHERE mt.has_unread = true) as threads_with_unread,
                AVG(thread_message_count.message_count) as avg_messages_per_thread
            FROM core.message_threads mt
            LEFT JOIN core.messages m ON m.thread_id = mt.id
                AND m.sent_at BETWEEN :date_from AND :date_to
            LEFT JOIN (
                SELECT thread_id, COUNT(*) as message_count
                FROM core.messages
                WHERE sent_at BETWEEN :date_from AND :date_to
                GROUP BY thread_id
            ) thread_message_count ON thread_message_count.thread_id = mt.id
            WHERE mt.created_at BETWEEN :date_from AND :date_to
        """
        )

        result = await self.session.execute(
            stmt,
            {
                "date_from": datetime.combine(date_from, datetime.min.time()),
                "date_to": datetime.combine(date_to, datetime.max.time()),
            },
        )

        row = result.fetchone()
        return dict(row._mapping) if row else {}


__all__ = [
    "GetAvailabilitySlotsQueryHandler",
    "GetBookingQueryHandler",
    "GetBookingsQueryHandler",
    "GetCustomer360QueryHandler",
    "GetDashboardStatsQueryHandler",
    "GetMessageThreadQueryHandler",
]
