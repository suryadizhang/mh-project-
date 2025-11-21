"""
Escalation Worker Tasks
Background jobs for handling customer support escalations
"""

from datetime import datetime
import logging

from core.database import get_sync_db
from models.escalation import Escalation, EscalationStatus
from services.ringcentral_service import get_ringcentral_service
from sqlalchemy.orm import Session
from workers.celery_config import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_escalation_notification(self, escalation_id: str):
    """
    Send WhatsApp/SMS notification to on-call admin when escalation is created

    Args:
        escalation_id: ID of the escalation

    Retries: 3 times with 60 second delay
    """
    db: Session = next(get_sync_db())

    try:
        # Query escalation directly (sync operation)
        escalation = (
            db.query(Escalation).filter(Escalation.id == escalation_id).first()
        )

        if not escalation:
            logger.error(f"Escalation {escalation_id} not found")
            return {"status": "error", "message": "Escalation not found"}

        # Send WhatsApp notification using async service
        import asyncio

        from services.whatsapp_notification_service import get_whatsapp_service

        whatsapp_service = get_whatsapp_service()

        # Run async function in sync context
        result = asyncio.run(
            whatsapp_service.send_escalation_alert(
                escalation_id=str(escalation.id),
                priority=escalation.priority,
                customer_phone=escalation.customer_phone,
                reason=escalation.reason,
                method=escalation.method,
                conversation_id=(
                    str(escalation.conversation_id)
                    if escalation.conversation_id
                    else None
                ),
            )
        )

        if result.get("success"):
            # Update escalation with notification details
            escalation.admin_notified_at = datetime.utcnow()
            escalation.admin_notification_sid = result.get("message_sid")
            escalation.admin_notification_channel = result.get("channel")
            escalation.admin_notification_status = "sent"
            db.commit()

            logger.info(
                f"Escalation notification sent for {escalation_id} via {result.get('channel')}"
            )

            return {
                "status": "success",
                "escalation_id": escalation_id,
                "message_id": result.get("message_sid"),
                "channel": result.get("channel"),
            }
        else:
            logger.error(
                f"Escalation notification failed: {result.get('error')}"
            )
            raise RuntimeError(f"Notification failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Failed to send escalation notification: {e!s}")

        # Record error in escalation
        try:
            if escalation:
                escalation.error_message = f"Notification failed: {e!s}"
                escalation.retry_count += 1
                db.commit()
        except Exception:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_customer_sms(
    self, escalation_id: str, message: str, admin_id: str | None = None
):
    """
    Send SMS to customer via escalation

    Args:
        escalation_id: ID of the escalation
        message: SMS message content
        admin_id: Optional ID of admin sending the message

    Retries: 3 times with 30 second delay
    """
    db: Session = next(get_sync_db())

    try:
        # Query escalation directly (sync operation)
        escalation = (
            db.query(Escalation).filter(Escalation.id == escalation_id).first()
        )

        if not escalation:
            logger.error(f"Escalation {escalation_id} not found")
            return {"status": "error", "message": "Escalation not found"}

        # Send SMS via RingCentral
        rc_service = get_ringcentral_service()

        if not rc_service.is_configured():
            raise RuntimeError("RingCentral not configured")

        result = rc_service.send_sms(
            to_phone=escalation.customer_phone,
            message=message,
        )

        # Record SMS sent
        escalation.sms_sent = True
        escalation.sms_sent_at = datetime.utcnow()

        # Update escalation status to in_progress if pending
        if (
            escalation.status == EscalationStatus.PENDING
            or escalation.status == EscalationStatus.ASSIGNED
        ):
            escalation.status = EscalationStatus.IN_PROGRESS

        db.commit()

        logger.info(
            f"SMS sent to customer {escalation.customer_phone} for escalation {escalation_id}"
        )

        return {
            "status": "success",
            "escalation_id": escalation_id,
            "message_id": result.get("message_id"),
            "sent_to": escalation.customer_phone,
        }

    except Exception as e:
        logger.error(f"Failed to send customer SMS: {e!s}")

        # Record error
        try:
            if escalation:
                escalation.error_message = f"SMS send failed: {e!s}"
                escalation.retry_count += 1
                db.commit()
        except Exception:
            pass

        # Retry
        raise self.retry(exc=e, countdown=30 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=0)
def retry_failed_escalations(self):
    """
    Periodic task to retry failed escalation notifications

    Runs every 5 minutes via Celery Beat
    Retries escalations in ERROR status with retry_count < 5
    """
    db: Session = next(get_sync_db())

    try:
        # Find escalations in ERROR status with retries remaining
        failed_escalations = (
            db.query(Escalation)
            .filter(
                Escalation.status == EscalationStatus.ERROR,
                Escalation.retry_count < 5,
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
                logger.error(
                    f"Failed to retry escalation {escalation.id}: {e!s}"
                )
                continue

        logger.info(f"Retried {retried_count} failed escalations")

        return {"status": "success", "retried": retried_count}

    except Exception as e:
        logger.error(f"Failed to retry escalations: {e!s}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@celery_app.task
def initiate_outbound_call(escalation_id: str, admin_id: str | None = None):
    """
    Initiate outbound call to customer via RingCentral

    Args:
        escalation_id: ID of the escalation
        admin_id: Optional ID of admin initiating the call
    """
    db: Session = next(get_sync_db())

    try:
        # Query escalation directly (sync operation)
        escalation = (
            db.query(Escalation).filter(Escalation.id == escalation_id).first()
        )

        if not escalation:
            logger.error(f"Escalation {escalation_id} not found")
            return {"status": "error", "message": "Escalation not found"}

        # Initiate call via RingCentral
        rc_service = get_ringcentral_service()

        if not rc_service.is_configured():
            raise RuntimeError("RingCentral not configured")

        result = rc_service.initiate_call(to_phone=escalation.customer_phone)

        # Record call initiated
        escalation.call_initiated = True
        escalation.call_initiated_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Outbound call initiated to {escalation.customer_phone} for escalation {escalation_id}"
        )

        return {
            "status": "success",
            "escalation_id": escalation_id,
            "call_id": result.get("call_id"),
            "to_phone": escalation.customer_phone,
        }

    except Exception as e:
        logger.error(f"Failed to initiate outbound call: {e!s}")

        # Record error
        try:
            if escalation:
                escalation.error_message = f"Call initiation failed: {e!s}"
                escalation.retry_count += 1
                db.commit()
        except Exception:
            pass

        return {"status": "error", "message": str(e)}

    finally:
        db.close()
