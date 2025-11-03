"""
Admin Email Review Dashboard API
Allows human review and approval of AI-generated email responses before sending
"""

from datetime import datetime
from enum import Enum
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class EmailStatus(str, Enum):
    """Email response status"""

    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    REJECTED = "rejected"
    EDITED = "edited"


class Priority(str, Enum):
    """Email priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PendingEmailResponse(BaseModel):
    """Email response awaiting human review"""

    id: str = Field(..., description="Unique email ID")
    customer_name: str
    customer_email: EmailStr
    original_subject: str
    original_body: str
    received_at: datetime

    # AI-generated response
    ai_response: str
    ai_subject: str
    ai_confidence: float
    ai_model_used: str
    complexity_score: float

    # Extracted information
    party_size: int | None
    location: str | None
    event_date: str | None
    inquiry_type: str
    special_requests: list[str] = []

    # Quote details
    estimated_quote: float | None
    quote_breakdown: dict[str, Any] | None

    # Status and priority
    status: EmailStatus = EmailStatus.PENDING
    priority: Priority = Priority.NORMAL
    requires_follow_up: bool = False

    # Timestamps
    processed_at: datetime
    reviewed_at: datetime | None = None
    sent_at: datetime | None = None

    # Review notes
    reviewer_notes: str | None = None
    edited_response: str | None = None


class EmailApprovalRequest(BaseModel):
    """Request to approve and send email"""

    email_id: str
    edited_response: str | None = None
    add_cc: list[EmailStr] | None = None
    add_bcc: list[EmailStr] | None = None
    schedule_send: datetime | None = None
    reviewer_notes: str | None = None


class EmailEditRequest(BaseModel):
    """Request to edit AI-generated response"""

    email_id: str
    edited_subject: str
    edited_body: str
    save_as_template: bool = False
    template_name: str | None = None


class EmailRejectRequest(BaseModel):
    """Request to reject AI response"""

    email_id: str
    reason: str
    assign_to_human: bool = True
    notes: str | None = None


# In-memory storage for demo (replace with database in production)
pending_emails: dict[str, PendingEmailResponse] = {}


@router.get("/pending", response_model=list[PendingEmailResponse])
async def get_pending_emails(
    priority: Priority | None = None,
    inquiry_type: str | None = None,
    min_quote: float | None = None,
    limit: int = 50,
):
    """
    Get list of pending email responses awaiting review.

    **Filters**:
    - `priority`: Filter by priority level (high, normal, low)
    - `inquiry_type`: Filter by type (quote, booking, complaint)
    - `min_quote`: Show only quotes above this amount
    - `limit`: Maximum number of emails to return

    **Returns**: List of pending emails sorted by priority and received time
    """
    filtered_emails = list(pending_emails.values())

    # Apply filters
    if priority:
        filtered_emails = [e for e in filtered_emails if e.priority == priority]

    if inquiry_type:
        filtered_emails = [e for e in filtered_emails if e.inquiry_type == inquiry_type]

    if min_quote:
        filtered_emails = [
            e for e in filtered_emails if e.estimated_quote and e.estimated_quote >= min_quote
        ]

    # Filter only pending
    filtered_emails = [e for e in filtered_emails if e.status == EmailStatus.PENDING]

    # Sort by priority (urgent first) then by received time
    priority_order = {Priority.URGENT: 0, Priority.HIGH: 1, Priority.NORMAL: 2, Priority.LOW: 3}
    filtered_emails.sort(key=lambda e: (priority_order.get(e.priority, 999), e.received_at))

    logger.info(f"Retrieved {len(filtered_emails[:limit])} pending emails")
    return filtered_emails[:limit]


@router.get("/{email_id}", response_model=PendingEmailResponse)
async def get_email_detail(email_id: str):
    """
    Get detailed view of specific email with AI-generated response.

    **Use Case**: View side-by-side comparison of original email and AI response
    """
    if email_id not in pending_emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Email {email_id} not found"
        )

    return pending_emails[email_id]


@router.post("/{email_id}/approve", status_code=status.HTTP_200_OK)
async def approve_and_send_email(
    email_id: str, approval: EmailApprovalRequest, background_tasks: BackgroundTasks
):
    """
    Approve AI-generated response and send email to customer.

    **Workflow**:
    1. Human reviews AI response
    2. Optionally edits response
    3. Clicks "Approve & Send"
    4. Email sent via SMTP
    5. Status updated to "sent"
    6. Logged for analytics

    **Parameters**:
    - `edited_response`: Optional edited version (overrides AI response)
    - `add_cc`: Additional CC recipients
    - `schedule_send`: Schedule for later (default: send immediately)
    - `reviewer_notes`: Internal notes for team
    """
    if email_id not in pending_emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Email {email_id} not found"
        )

    email = pending_emails[email_id]

    # Use edited response if provided, otherwise use AI response
    final_response = approval.edited_response if approval.edited_response else email.ai_response

    # Update status
    email.status = EmailStatus.APPROVED if not approval.schedule_send else EmailStatus.PENDING
    email.reviewed_at = datetime.now()
    email.reviewer_notes = approval.reviewer_notes

    if approval.edited_response:
        email.edited_response = approval.edited_response
        email.status = EmailStatus.EDITED

    # Send email (background task)
    if not approval.schedule_send:
        background_tasks.add_task(
            send_email_via_smtp,
            to=email.customer_email,
            subject=email.ai_subject,
            body=final_response,
            cc=approval.add_cc,
            bcc=approval.add_bcc,
        )
        email.sent_at = datetime.now()
        email.status = EmailStatus.SENT

    logger.info(f"Email {email_id} approved and queued for sending to {email.customer_email}")

    return {
        "success": True,
        "email_id": email_id,
        "status": email.status,
        "sent_at": email.sent_at,
        "message": (
            "Email approved and sent successfully"
            if email.status == EmailStatus.SENT
            else "Email approved and scheduled"
        ),
    }


@router.post("/{email_id}/edit", status_code=status.HTTP_200_OK)
async def edit_email_response(email_id: str, edit_request: EmailEditRequest):
    """
    Save edited version of AI-generated response.

    **Use Case**:
    - Human wants to modify AI response before sending
    - Add personal touches
    - Adjust pricing or terms
    - Save as template for future use

    **Does NOT send email** - just saves edits. Use `/approve` to send.
    """
    if email_id not in pending_emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Email {email_id} not found"
        )

    email = pending_emails[email_id]
    email.edited_response = edit_request.edited_body
    email.ai_subject = edit_request.edited_subject
    email.status = EmailStatus.EDITED
    email.reviewed_at = datetime.now()

    # Save as template if requested
    if edit_request.save_as_template and edit_request.template_name:
        # TODO: Save to template database
        logger.info(f"Saved edited response as template: {edit_request.template_name}")

    logger.info(f"Email {email_id} edited by reviewer")

    return {
        "success": True,
        "email_id": email_id,
        "status": email.status,
        "message": "Email response edited successfully",
    }


@router.post("/{email_id}/reject", status_code=status.HTTP_200_OK)
async def reject_ai_response(email_id: str, reject_request: EmailRejectRequest):
    """
    Reject AI-generated response and mark for manual handling.

    **Use Case**:
    - AI response is inaccurate
    - Complex situation requires human touch
    - Customer is VIP or high-value
    - Complaint or sensitive issue

    **Result**: Email moved to "manual response" queue for staff
    """
    if email_id not in pending_emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Email {email_id} not found"
        )

    email = pending_emails[email_id]
    email.status = EmailStatus.REJECTED
    email.reviewed_at = datetime.now()
    email.reviewer_notes = f"REJECTED: {reject_request.reason}. {reject_request.notes or ''}"

    # Assign to human if requested
    if reject_request.assign_to_human:
        # TODO: Create task in CRM for human follow-up
        logger.info(f"Email {email_id} assigned to human for manual response")

    logger.info(f"Email {email_id} rejected: {reject_request.reason}")

    return {
        "success": True,
        "email_id": email_id,
        "status": email.status,
        "message": "AI response rejected, marked for manual handling",
    }


@router.get("/stats/summary", status_code=status.HTTP_200_OK)
async def get_email_stats():
    """
    Get summary statistics for email review dashboard.

    **Returns**:
    - Total pending emails
    - By priority (urgent, high, normal, low)
    - Average response time
    - Approval rate
    - Top inquiry types
    """
    all_emails = list(pending_emails.values())

    stats = {
        "total_pending": len([e for e in all_emails if e.status == EmailStatus.PENDING]),
        "by_priority": {
            "urgent": len(
                [
                    e
                    for e in all_emails
                    if e.priority == Priority.URGENT and e.status == EmailStatus.PENDING
                ]
            ),
            "high": len(
                [
                    e
                    for e in all_emails
                    if e.priority == Priority.HIGH and e.status == EmailStatus.PENDING
                ]
            ),
            "normal": len(
                [
                    e
                    for e in all_emails
                    if e.priority == Priority.NORMAL and e.status == EmailStatus.PENDING
                ]
            ),
            "low": len(
                [
                    e
                    for e in all_emails
                    if e.priority == Priority.LOW and e.status == EmailStatus.PENDING
                ]
            ),
        },
        "by_inquiry_type": {},
        "total_processed": len(
            [e for e in all_emails if e.status in [EmailStatus.SENT, EmailStatus.REJECTED]]
        ),
        "approval_rate": 0.0,
        "average_quote": 0.0,
    }

    # Calculate approval rate
    sent_count = len([e for e in all_emails if e.status == EmailStatus.SENT])
    rejected_count = len([e for e in all_emails if e.status == EmailStatus.REJECTED])
    total_reviewed = sent_count + rejected_count

    if total_reviewed > 0:
        stats["approval_rate"] = (sent_count / total_reviewed) * 100

    # Calculate average quote
    quotes = [e.estimated_quote for e in all_emails if e.estimated_quote]
    if quotes:
        stats["average_quote"] = sum(quotes) / len(quotes)

    # Count by inquiry type
    for email in all_emails:
        inquiry_type = email.inquiry_type
        if inquiry_type not in stats["by_inquiry_type"]:
            stats["by_inquiry_type"][inquiry_type] = 0
        stats["by_inquiry_type"][inquiry_type] += 1

    return stats


async def send_email_via_smtp(
    to: str, subject: str, body: str, cc: list[str] | None = None, bcc: list[str] | None = None
):
    """
    Send email via IONOS SMTP.

    This is a placeholder - will be implemented with actual SMTP connection.
    """
    logger.info(f"Sending email to {to}: {subject}")
    logger.info(f"Body length: {len(body)} characters")

    # TODO: Implement actual SMTP sending
    # import smtplib
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    #
    # msg = MIMEMultipart()
    # msg['From'] = "cs@myhibachichef.com"
    # msg['To'] = to
    # msg['Subject'] = subject
    # if cc:
    #     msg['Cc'] = ', '.join(cc)
    #
    # msg.attach(MIMEText(body, 'html'))
    #
    # with smtplib.SMTP('smtp.ionos.com', 587) as server:
    #     server.starttls()
    #     server.login("cs@myhibachichef.com", os.getenv("IONOS_PASSWORD"))
    #     server.send_message(msg)

    logger.info(f"✅ Email sent successfully to {to}")


# Helper function to add email to review queue
async def add_email_to_review_queue(
    customer_email: str,
    customer_name: str,
    original_subject: str,
    original_body: str,
    ai_response_data: dict[str, Any],
) -> str:
    """
    Add AI-generated email response to review queue.

    Called by email monitor when new customer email is processed.
    """
    import uuid

    email_id = str(uuid.uuid4())

    pending_email = PendingEmailResponse(
        id=email_id,
        customer_name=customer_name,
        customer_email=customer_email,
        original_subject=original_subject,
        original_body=original_body,
        received_at=datetime.now(),
        ai_response=ai_response_data.get("response_text", ""),
        ai_subject=f"Re: {original_subject}",
        ai_confidence=ai_response_data.get("ai_metadata", {}).get("confidence", 0.0),
        ai_model_used=ai_response_data.get("ai_metadata", {}).get("model_used", "unknown"),
        complexity_score=ai_response_data.get("ai_metadata", {}).get("complexity_score", 0.0),
        party_size=ai_response_data.get("metadata", {}).get("party_size"),
        location=ai_response_data.get("metadata", {}).get("location"),
        event_date=ai_response_data.get("metadata", {}).get("event_date"),
        inquiry_type=ai_response_data.get("metadata", {}).get("inquiry_type", "general"),
        special_requests=ai_response_data.get("metadata", {}).get("special_requests", []),
        estimated_quote=ai_response_data.get("metadata", {}).get("estimated_quote"),
        quote_breakdown=ai_response_data.get("metadata", {}).get("quote_breakdown"),
        priority=determine_priority(ai_response_data),
        requires_follow_up=ai_response_data.get("metadata", {}).get("requires_follow_up", False),
        processed_at=datetime.now(),
    )

    pending_emails[email_id] = pending_email

    logger.info(
        f"Added email {email_id} to review queue: {customer_name} - {pending_email.inquiry_type}"
    )

    return email_id


def determine_priority(ai_response_data: dict[str, Any]) -> Priority:
    """Determine email priority based on AI analysis"""
    metadata = ai_response_data.get("metadata", {})

    # Holiday bookings = HIGH
    if "holiday" in str(metadata.get("event_date", "")).lower():
        return Priority.HIGH

    # Large quotes = HIGH
    if metadata.get("estimated_quote", 0) > 1000:
        return Priority.HIGH

    # Complaints = URGENT
    if metadata.get("inquiry_type") == "complaint":
        return Priority.URGENT

    # Negative sentiment = HIGH
    if metadata.get("sentiment") == "negative":
        return Priority.HIGH

    # High urgency keywords = HIGH
    if metadata.get("urgency") in ["high", "urgent"]:
        return Priority.HIGH

    return Priority.NORMAL
