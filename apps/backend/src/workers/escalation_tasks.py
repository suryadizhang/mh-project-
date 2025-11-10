"""
Escalation Worker Tasks
Background jobs for handling customer support escalations
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session
from workers.celery_config import celery_app
from core.database import get_db_session
from models.escalation import Escalation, EscalationStatus
from services.escalation_service import EscalationService
from services.ringcentral_service import get_ringcentral_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_escalation_notification(self, escalation_id: str):
    """
    Send SMS notification to on-call admin when escalation is created

    Args:
        escalation_id: ID of the escalation

    Retries: 3 times with 60 second delay
    """
    db: Session = next(get_db_session())

    try:
        service = EscalationService(db)
        escalation = await service.get_escalation(escalation_id)

        if not escalation:
            logger.error(f"Escalation {escalation_id} not found")
            return {"status": "error", "message": "Escalation not found"}

        # Get on-call admin phone (TODO: implement on-call rotation)
        # For now, use a configured phone number
        import os

        on_call_phone = os.getenv("ON_CALL_ADMIN_PHONE", "+15555551234")

        # Compose notification message
        message = (
            f"🚨 NEW ESCALATION\n"
            f"Priority: {escalation.priority.upper()}\n"
            f"Customer: {escalation.phone}\n"
            f"Reason: {escalation.reason[:100]}...\n"
            f"Method: {escalation.preferred_method}\n"
            f"View: https://admin.myhibachi.com/inbox/escalations/{escalation_id}"
        )

        # Send SMS via RingCentral
        rc_service = get_ringcentral_service()

        if not rc_service.is_configured():
            logger.warning("RingCentral not configured, skipping notification")
            return {"status": "skipped", "reason": "RingCentral not configured"}

        result = rc_service.send_sms(
            to_phone=on_call_phone,
            message=message,
            metadata={"escalation_id": escalation_id, "type": "admin_notification"},
        )

        logger.info(
            f"Escalation notification sent to {on_call_phone} for escalation {escalation_id}"
        )

        return {
            "status": "success",
            "escalation_id": escalation_id,
            "message_id": result.get("message_id"),
            "sent_to": on_call_phone,
        }

    except Exception as e:
        logger.error(f"Failed to send escalation notification: {str(e)}")

        # Record error in escalation
        try:
            await service.record_error(escalation_id, f"Notification failed: {str(e)}")
        except Exception:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_customer_sms(self, escalation_id: str, message: str, admin_id: Optional[str] = None):
    """
    Send SMS to customer via escalation

    Args:
        escalation_id: ID of the escalation
        message: SMS message content
        admin_id: Optional ID of admin sending the message

    Retries: 3 times with 30 second delay
    """
    db: Session = next(get_db_session())

    try:
        service = EscalationService(db)
        escalation = await service.get_escalation(escalation_id)

        if not escalation:
            logger.error(f"Escalation {escalation_id} not found")
            return {"status": "error", "message": "Escalation not found"}

        # Check customer consent
        if escalation.customer_consent != "true":
            logger.warning(f"Customer did not consent to SMS for escalation {escalation_id}")
            return {"status": "error", "message": "Customer did not consent to SMS"}

        # Send SMS via RingCentral
        rc_service = get_ringcentral_service()

        if not rc_service.is_configured():
            raise RuntimeError("RingCentral not configured")

        result = rc_service.send_sms(
            to_phone=escalation.phone,
            message=message,
            metadata={
                "escalation_id": escalation_id,
                "admin_id": admin_id,
                "type": "customer_reply",
            },
        )

        # Record SMS sent
        await service.record_sms_sent(escalation_id)

        # Update escalation status to in_progress if pending
        if (
            escalation.status == EscalationStatus.PENDING
            or escalation.status == EscalationStatus.ASSIGNED
        ):
            await service.update_status(escalation_id, EscalationStatus.IN_PROGRESS.value)

        logger.info(f"SMS sent to customer {escalation.phone} for escalation {escalation_id}")

        return {
            "status": "success",
            "escalation_id": escalation_id,
            "message_id": result.get("message_id"),
            "sent_to": escalation.phone,
            "sent_at": result.get("sent_at"),
        }

    except Exception as e:
        logger.error(f"Failed to send customer SMS: {str(e)}")

        # Record error
        try:
            await service.record_error(escalation_id, f"SMS send failed: {str(e)}")
        except Exception:
            pass

        # Retry
        raise self.retry(exc=e, countdown=30 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=5, default_retry_delay=300)
def retry_failed_escalations(self):
    """
    Periodic task to retry failed escalation notifications

    Runs every 5 minutes via Celery Beat
    Retries escalations in ERROR status with retry_count < 5
    """
    db: Session = next(get_db_session())

    try:
        service = EscalationService(db)

        # Find escalations in ERROR status with retries remaining
        failed_escalations = (
            db.query(Escalation)
            .filter(
                Escalation.status == EscalationStatus.ERROR,
                Escalation.retry_count < "5",
            )
            .all()
        )

        if not failed_escalations:
            logger.info("No failed escalations to retry")
            return {"status": "success", "retried": 0}

        retried_count = 0

        for escalation in failed_escalations:
            try:
                logger.info(
                    f"Retrying failed escalation {escalation.id}, "
                    f"attempt {int(escalation.retry_count) + 1}"
                )

                # Reset status to PENDING
                escalation.status = EscalationStatus.PENDING
                escalation.error_message = None
                db.commit()

                # Re-queue notification
                send_escalation_notification.delay(str(escalation.id))

                retried_count += 1

            except Exception as e:
                logger.error(f"Failed to retry escalation {escalation.id}: {str(e)}")
                continue

        logger.info(f"Retried {retried_count} failed escalations")

        return {"status": "success", "retried": retried_count}

    except Exception as e:
        logger.error(f"Failed to retry escalations: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@celery_app.task
def initiate_outbound_call(escalation_id: str, admin_id: Optional[str] = None):
    """
    Initiate outbound call to customer via RingCentral

    Args:
        escalation_id: ID of the escalation
        admin_id: Optional ID of admin initiating the call
    """
    db: Session = next(get_db_session())

    try:
        service = EscalationService(db)
        escalation = await service.get_escalation(escalation_id)

        if not escalation:
            logger.error(f"Escalation {escalation_id} not found")
            return {"status": "error", "message": "Escalation not found"}

        # Initiate call via RingCentral
        rc_service = get_ringcentral_service()

        if not rc_service.is_configured():
            raise RuntimeError("RingCentral not configured")

        result = rc_service.initiate_call(to_phone=escalation.phone)

        # Record call initiated
        await service.record_call_initiated(escalation_id)

        logger.info(f"Outbound call initiated to {escalation.phone} for escalation {escalation_id}")

        return {
            "status": "success",
            "escalation_id": escalation_id,
            "call_id": result.get("call_id"),
            "to_phone": escalation.phone,
        }

    except Exception as e:
        logger.error(f"Failed to initiate outbound call: {str(e)}")

        # Record error
        try:
            await service.record_error(escalation_id, f"Call initiation failed: {str(e)}")
        except Exception:
            pass

        return {"status": "error", "message": str(e)}

    finally:
        db.close()
