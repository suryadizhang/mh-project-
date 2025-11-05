"""
Command handlers for CRM operations.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from api.app.cqrs.base import (
    CommandHandler,
    CommandResult,
    EventStore,
    OutboxProcessor,
)
from api.app.cqrs.crm_operations import *
from api.app.models.core import (
    Booking,
    Customer,
    Message,
    MessageThread,
    Payment,
)
from api.app.models.events import IdempotencyKey
from api.app.utils.encryption import FieldEncryption
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class CreateBookingCommandHandler(CommandHandler):
    """Handle booking creation with full validation and event sourcing."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.event_store = EventStore(session)
        self.outbox_processor = OutboxProcessor(session)
        self.encryption = FieldEncryption()

    async def handle(self, command: CreateBookingCommand) -> CommandResult:
        """Create a new booking with proper validation and event emission."""
        try:
            # Check idempotency
            if command.idempotency_key:
                existing = await self._check_idempotency(
                    command.idempotency_key, "CreateBookingCommand"
                )
                if existing:
                    return existing

            # Validate slot availability
            is_available = await self._check_slot_availability(
                command.date, command.slot, command.total_guests
            )
            if not is_available:
                return CommandResult(
                    success=False,
                    error=f"Slot {command.slot} on {command.date} is not available for {command.total_guests} guests",
                )

            # Find or create customer
            customer = await self._find_or_create_customer(
                command.customer_email, command.customer_name, command.customer_phone
            )

            # Create booking
            booking_id = uuid4()
            booking = Booking(
                id=booking_id,
                customer_id=customer.id,
                date=command.date,
                slot=command.slot,
                total_guests=command.total_guests,
                price_per_person_cents=command.price_per_person_cents,
                total_due_cents=command.total_due_cents,
                deposit_due_cents=command.deposit_due_cents,
                special_requests=(
                    self.encryption.encrypt(command.special_requests)
                    if command.special_requests
                    else None
                ),
                source=command.source,
                ai_conversation_id=command.ai_conversation_id,
                status="confirmed",
                balance_due_cents=command.total_due_cents - command.deposit_due_cents,
                created_at=datetime.utcnow(),
            )

            self.session.add(booking)

            # Create domain event
            event = BookingCreated(
                aggregate_id=booking_id,
                customer_email=command.customer_email,
                customer_name=command.customer_name,
                customer_phone=command.customer_phone,
                date=command.date,
                slot=command.slot,
                total_guests=command.total_guests,
                total_due_cents=command.total_due_cents,
                deposit_due_cents=command.deposit_due_cents,
                source=command.source,
                special_requests=command.special_requests,
                ai_conversation_id=command.ai_conversation_id,
            )

            # Store events
            domain_events = await self.event_store.append_events([event])

            # Create outbox entries for integrations
            await self.outbox_processor.create_outbox_entries(
                domain_events,
                targets=["email", "stripe"] if command.deposit_due_cents > 0 else ["email"],
            )

            # Save idempotency
            if command.idempotency_key:
                await self._save_idempotency(
                    command.idempotency_key,
                    "CreateBookingCommand",
                    {"booking_id": str(booking_id), "customer_id": str(customer.id)},
                )

            await self.session.commit()

            return CommandResult(
                success=True,
                data={
                    "booking_id": str(booking_id),
                    "customer_id": str(customer.id),
                    "confirmation_number": f"MH-{booking_id.hex[:8].upper()}",
                },
                events=[event],
            )

        except Exception as e:
            await self.session.rollback()
            return CommandResult(success=False, error=str(e))

    async def _check_slot_availability(self, date, slot: str, party_size: int) -> bool:
        """Check if the requested slot is available."""
        # Get existing bookings for that date/slot
        stmt = select(Booking.total_guests).where(
            and_(
                Booking.date == date,
                Booking.slot == slot,
                Booking.status.in_(["confirmed", "pending"]),
            )
        )

        result = await self.session.execute(stmt)
        existing_guests = sum(row[0] for row in result.fetchall())

        # Assume max 50 guests per slot (configurable)
        max_capacity = 50
        return (existing_guests + party_size) <= max_capacity

    async def _find_or_create_customer(self, email: str, name: str, phone: str) -> Customer:
        """Find existing customer or create new one."""
        # Try to find by email first
        encrypted_email = self.encryption.encrypt(email)

        stmt = select(Customer).where(Customer.email_encrypted == encrypted_email)
        result = await self.session.execute(stmt)
        customer = result.scalar_one_or_none()

        if customer:
            # Update name/phone if they've changed
            needs_update = False
            decrypted_name = self.encryption.decrypt(customer.name_encrypted)
            decrypted_phone = self.encryption.decrypt(customer.phone_encrypted)

            if decrypted_name != name:
                customer.name_encrypted = self.encryption.encrypt(name)
                needs_update = True

            if decrypted_phone != phone:
                customer.phone_encrypted = self.encryption.encrypt(phone)
                needs_update = True

            if needs_update:
                customer.updated_at = datetime.utcnow()

            return customer

        # Create new customer
        customer_id = uuid4()
        customer = Customer(
            id=customer_id,
            email_encrypted=encrypted_email,
            name_encrypted=self.encryption.encrypt(name),
            phone_encrypted=self.encryption.encrypt(phone),
            source="booking",
            created_at=datetime.utcnow(),
        )

        self.session.add(customer)
        await self.session.flush()  # Get the ID

        return customer

    async def _check_idempotency(self, key: str, command_type: str) -> CommandResult | None:
        """Check if this command was already processed."""
        stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
        result = await self.session.execute(stmt)
        idem = result.scalar_one_or_none()

        if idem:
            if idem.status == "completed":
                return CommandResult(success=True, data=idem.result)
            elif idem.status == "failed":
                return CommandResult(success=False, error="Command previously failed")
            else:
                return CommandResult(success=False, error="Command is still processing")

        return None

    async def _save_idempotency(self, key: str, command_type: str, result_data: dict[str, Any]):
        """Save idempotency result."""
        from datetime import timedelta

        idem = IdempotencyKey(
            key=key,
            command_type=command_type,
            result=result_data,
            status="completed",
            completed_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),  # Keep for a week
        )

        self.session.add(idem)


class RecordPaymentCommandHandler(CommandHandler):
    """Handle payment recording with validation."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.event_store = EventStore(session)
        self.outbox_processor = OutboxProcessor(session)

    async def handle(self, command: RecordPaymentCommand) -> CommandResult:
        """Record a payment for a booking."""
        try:
            # Check idempotency
            if command.idempotency_key:
                existing = await self._check_idempotency(
                    command.idempotency_key, "RecordPaymentCommand"
                )
                if existing:
                    return existing

            # Validate booking exists
            booking_stmt = select(Booking).where(Booking.id == command.booking_id)
            booking_result = await self.session.execute(booking_stmt)
            booking = booking_result.scalar_one_or_none()

            if not booking:
                return CommandResult(success=False, error=f"Booking {command.booking_id} not found")

            if booking.status == "cancelled":
                return CommandResult(
                    success=False, error="Cannot record payment for cancelled booking"
                )

            # Check payment doesn't exceed what's due
            existing_payments_stmt = select(Payment.amount_cents).where(
                Payment.booking_id == command.booking_id
            )
            payments_result = await self.session.execute(existing_payments_stmt)
            total_paid = sum(row[0] for row in payments_result.fetchall())

            if (total_paid + command.amount_cents) > booking.total_due_cents:
                return CommandResult(
                    success=False,
                    error=f"Payment amount ({command.amount_cents}) would exceed remaining balance",
                )

            # Create payment record
            payment_id = uuid4()
            payment = Payment(
                id=payment_id,
                booking_id=command.booking_id,
                amount_cents=command.amount_cents,
                payment_method=command.payment_method,
                payment_reference=command.payment_reference,
                notes=command.notes,
                processed_by=command.processed_by,
                processed_at=datetime.utcnow(),
            )

            self.session.add(payment)

            # Update booking balance
            new_balance = booking.balance_due_cents - command.amount_cents
            booking.balance_due_cents = new_balance
            booking.updated_at = datetime.utcnow()

            # Mark as paid if balance is zero
            if new_balance == 0:
                booking.payment_status = "paid"
            elif total_paid + command.amount_cents >= booking.deposit_due_cents:
                booking.payment_status = "deposit_paid"

            # Create domain event
            event = PaymentRecorded(
                aggregate_id=payment_id,
                booking_id=command.booking_id,
                amount_cents=command.amount_cents,
                payment_method=command.payment_method,
                payment_reference=command.payment_reference,
                processed_by=command.processed_by,
                notes=command.notes,
            )

            # Store event
            domain_events = await self.event_store.append_events([event])

            # Create outbox entries (for confirmation emails, etc.)
            await self.outbox_processor.create_outbox_entries(domain_events, targets=["email"])

            # Save idempotency
            if command.idempotency_key:
                await self._save_idempotency(
                    command.idempotency_key,
                    "RecordPaymentCommand",
                    {"payment_id": str(payment_id), "new_balance": new_balance},
                )

            await self.session.commit()

            return CommandResult(
                success=True,
                data={
                    "payment_id": str(payment_id),
                    "new_balance_cents": new_balance,
                    "payment_status": booking.payment_status,
                },
                events=[event],
            )

        except Exception as e:
            await self.session.rollback()
            return CommandResult(success=False, error=str(e))

    async def _check_idempotency(self, key: str, command_type: str) -> CommandResult | None:
        """Check if this command was already processed."""
        stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
        result = await self.session.execute(stmt)
        idem = result.scalar_one_or_none()

        if idem:
            if idem.status == "completed":
                return CommandResult(success=True, data=idem.result)
            elif idem.status == "failed":
                return CommandResult(success=False, error="Command previously failed")
            else:
                return CommandResult(success=False, error="Command is still processing")

        return None

    async def _save_idempotency(self, key: str, command_type: str, result_data: dict[str, Any]):
        """Save idempotency result."""
        from datetime import timedelta

        idem = IdempotencyKey(
            key=key,
            command_type=command_type,
            result=result_data,
            status="completed",
            completed_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        self.session.add(idem)


class ReceiveMessageCommandHandler(CommandHandler):
    """Handle incoming messages from customers."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.event_store = EventStore(session)
        self.outbox_processor = OutboxProcessor(session)
        self.encryption = FieldEncryption()

    async def handle(self, command: ReceiveMessageCommand) -> CommandResult:
        """Process incoming customer message."""
        try:
            # Check idempotency
            if command.idempotency_key:
                existing = await self._check_idempotency(
                    command.idempotency_key, "ReceiveMessageCommand"
                )
                if existing:
                    return existing

            # Find or create message thread
            thread = None

            if command.thread_id:
                # Use existing thread
                thread_stmt = select(MessageThread).where(MessageThread.id == command.thread_id)
                thread_result = await self.session.execute(thread_stmt)
                thread = thread_result.scalar_one_or_none()

            if not thread:
                # Find thread by phone number
                encrypted_phone = self.encryption.encrypt(command.phone_number)
                thread_stmt = (
                    select(MessageThread)
                    .where(MessageThread.phone_number_encrypted == encrypted_phone)
                    .order_by(MessageThread.created_at.desc())
                )
                thread_result = await self.session.execute(thread_stmt)
                thread = thread_result.first()

                if thread:
                    thread = thread[0]  # Extract from Row object

            if not thread:
                # Create new thread
                thread_id = uuid4()
                thread = MessageThread(
                    id=thread_id,
                    phone_number_encrypted=self.encryption.encrypt(command.phone_number),
                    customer_id=None,  # Will be linked later if customer found
                    status="active",
                    created_at=datetime.utcnow(),
                )
                self.session.add(thread)
                await self.session.flush()

            # Create message record
            message_id = uuid4()
            message = Message(
                id=message_id,
                thread_id=thread.id,
                content_encrypted=self.encryption.encrypt(command.content),
                direction="inbound",
                external_message_id=command.external_message_id,
                source=command.source,
                sent_at=command.received_at,
                created_at=datetime.utcnow(),
            )

            self.session.add(message)

            # Update thread
            thread.last_message_at = command.received_at
            thread.has_unread = True
            thread.updated_at = datetime.utcnow()

            # Create domain event
            event = MessageReceived(
                aggregate_id=thread.id,
                thread_id=thread.id,
                phone_number=command.phone_number,
                content=command.content,
                received_at=command.received_at,
                external_message_id=command.external_message_id,
                source=command.source,
            )

            # Store event
            domain_events = await self.event_store.append_events([event])

            # Create outbox entry for AI processing
            await self.outbox_processor.create_outbox_entries(
                domain_events, targets=["ai_processing"]
            )

            # Save idempotency
            if command.idempotency_key:
                await self._save_idempotency(
                    command.idempotency_key,
                    "ReceiveMessageCommand",
                    {"message_id": str(message_id), "thread_id": str(thread.id)},
                )

            await self.session.commit()

            return CommandResult(
                success=True,
                data={
                    "message_id": str(message_id),
                    "thread_id": str(thread.id),
                    "created_new_thread": thread.created_at == thread.updated_at,
                },
                events=[event],
            )

        except Exception as e:
            await self.session.rollback()
            return CommandResult(success=False, error=str(e))

    async def _check_idempotency(self, key: str, command_type: str) -> CommandResult | None:
        """Check if this command was already processed."""
        stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
        result = await self.session.execute(stmt)
        idem = result.scalar_one_or_none()

        if idem:
            if idem.status == "completed":
                return CommandResult(success=True, data=idem.result)
            elif idem.status == "failed":
                return CommandResult(success=False, error="Command previously failed")
            else:
                return CommandResult(success=False, error="Command is still processing")

        return None

    async def _save_idempotency(self, key: str, command_type: str, result_data: dict[str, Any]):
        """Save idempotency result."""
        from datetime import timedelta

        idem = IdempotencyKey(
            key=key,
            command_type=command_type,
            result=result_data,
            status="completed",
            completed_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        self.session.add(idem)
