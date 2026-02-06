"""
Payment Instructions Service

Sends payment instructions to customers via SMS (primary) or Email (fallback/receipts).
Automatically selects the best channel based on available customer data.

Strategy:
- SMS: Quick instructions, payment links, reminders (primary contact method)
- Email: Receipts, detailed instructions, too long for SMS, no phone available

As per user requirement:
"text is our main primary contact to customer, and email is for receipt
or other complex stuff that too long or cant be done through text"
"""

import logging
import os
from decimal import Decimal
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class InstructionChannel(str, Enum):
    """Delivery channel for payment instructions"""

    SMS = "sms"
    EMAIL = "email"
    BOTH = "both"


class PaymentInstructionsService:
    """
    Send payment instructions via SMS (primary) or Email (fallback).

    Features:
    - Automatic channel selection based on data availability
    - SMS for quick instructions and reminders
    - Email for receipts and complex instructions
    - Phone number prominently displayed in all communications
    - Branded templates
    """

    def __init__(self):
        """Initialize payment instructions service"""
        self.business_phone = os.getenv("BUSINESS_PHONE", "+19167408768")
        self.business_email = os.getenv("BUSINESS_EMAIL", "cs@myhibachichef.com")
        self.business_name = os.getenv("BUSINESS_NAME", "My Hibachi Chef")
        self.zelle_email = os.getenv("ZELLE_EMAIL", "myhibachichef@gmail.com")
        self.zelle_phone = os.getenv("ZELLE_PHONE", "+19167408768")
        self.venmo_username = os.getenv("VENMO_USERNAME", "@myhibachichef")

    async def send_payment_instructions(
        self,
        customer_name: str,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        booking_id: int | None = None,
        amount: Decimal | None = None,
        payment_methods: list[str] | None = None,
        include_alternative_payer: bool = False,
    ) -> dict[str, Any]:
        """
        Send payment instructions using the best available channel.

        Logic:
        1. If phone available → SMS (primary)
        2. If no phone but email → Email
        3. If both available and amount > $500 → BOTH (SMS + Email receipt)

        Args:
            customer_name: Customer name
            customer_phone: Phone number (preferred)
            customer_email: Email address (fallback)
            booking_id: Booking reference
            amount: Payment amount
            payment_methods: List of accepted methods (stripe, zelle, venmo)
            include_alternative_payer: Show alternative payer instructions

        Returns:
            Delivery status and details
        """
        if payment_methods is None:
            payment_methods = ["stripe", "zelle", "venmo"]

        # Determine channel
        channel = self._select_channel(customer_phone, customer_email, amount)

        result = {
            "success": False,
            "channel": channel,
            "sms_sent": False,
            "email_sent": False,
            "error": None,
        }

        try:
            # Send SMS if phone available
            if customer_phone and channel in [
                InstructionChannel.SMS,
                InstructionChannel.BOTH,
            ]:
                sms_result = await self._send_sms_instructions(
                    phone=customer_phone,
                    name=customer_name,
                    booking_id=booking_id,
                    amount=amount,
                    payment_methods=payment_methods,
                )
                result["sms_sent"] = sms_result["success"]
                if not sms_result["success"]:
                    result["error"] = sms_result.get("error")

            # Send Email if needed
            if customer_email and channel in [
                InstructionChannel.EMAIL,
                InstructionChannel.BOTH,
            ]:
                email_result = await self._send_email_instructions(
                    email=customer_email,
                    name=customer_name,
                    booking_id=booking_id,
                    amount=amount,
                    payment_methods=payment_methods,
                    include_alternative_payer=include_alternative_payer,
                )
                result["email_sent"] = email_result["success"]
                if not email_result["success"] and not result["sms_sent"]:
                    result["error"] = email_result.get("error")

            # Success if at least one channel worked
            result["success"] = result["sms_sent"] or result["email_sent"]

            return result

        except Exception as e:
            logger.exception(f"Payment instructions failed: {e}")
            result["error"] = str(e)
            return result

    def _select_channel(
        self, phone: str | None, email: str | None, amount: Decimal | None
    ) -> InstructionChannel:
        """
        Select best channel for payment instructions.

        Rules:
        - Phone only → SMS
        - Email only → Email
        - Both + amount > $500 → BOTH (SMS quick, Email receipt)
        - Both + amount ≤ $500 → SMS (faster)
        """
        if not phone and not email:
            raise ValueError("No contact information available")

        if phone and not email:
            return InstructionChannel.SMS

        if email and not phone:
            return InstructionChannel.EMAIL

        # Both available
        if amount and amount > Decimal("500.00"):
            # Large payment → Send both (SMS for quick action, Email for record)
            return InstructionChannel.BOTH
        else:
            # Small payment → SMS only (faster, cheaper)
            return InstructionChannel.SMS

    async def _send_sms_instructions(
        self,
        phone: str,
        name: str,
        booking_id: int | None,
        amount: Decimal | None,
        payment_methods: list[str],
    ) -> dict[str, Any]:
        """Send quick payment instructions via SMS"""
        try:
            # Import SMS service
            from services.whatsapp_notification_service import get_whatsapp_service

            # Build concise SMS message
            message = self._build_sms_message(name, booking_id, amount, payment_methods)

            # Send via WhatsApp/SMS service
            service = get_whatsapp_service()
            result = await service._send_sms(phone, message)

            return result

        except Exception as e:
            logger.exception(f"SMS instructions failed: {e}")
            return {"success": False, "error": str(e)}

    def _build_sms_message(
        self,
        name: str,
        booking_id: int | None,
        amount: Decimal | None,
        payment_methods: list[str],
    ) -> str:
        """Build SMS payment instructions (max 160 chars per segment)"""

        # Compact format for SMS
        lines = [
            f"Hi {name.split()[0]}! 🎉",  # First name only
            "",
            f"Payment needed{f': ${amount:.2f}' if amount else ''}",
        ]

        if booking_id:
            lines.append(f"Booking #{booking_id}")

        lines.append("")
        lines.append("📲 Pay via:")

        # List payment methods compactly
        if "stripe" in payment_methods:
            lines.append("💳 Card: myhibachichef.com/pay")

        if "zelle" in payment_methods:
            lines.append(f"⚡ Zelle: {self.zelle_phone}")
            lines.append(f"   Email: {self.zelle_email}")

        if "venmo" in payment_methods:
            lines.append(f"💙 Venmo: {self.venmo_username}")

        lines.extend(["", f"Questions? Call {self.business_phone}", "", "- My Hibachi Chef Team"])

        return "\n".join(lines)

    async def _send_email_instructions(
        self,
        email: str,
        name: str,
        booking_id: int | None,
        amount: Decimal | None,
        payment_methods: list[str],
        include_alternative_payer: bool = False,
    ) -> dict[str, Any]:
        """Send detailed payment instructions via Email"""
        try:
            # Import email service
            from services.email_service import EmailService

            email_service = EmailService()

            # Build detailed HTML email
            html_content = self._build_email_html(
                name=name,
                booking_id=booking_id,
                amount=amount,
                payment_methods=payment_methods,
                include_alternative_payer=include_alternative_payer,
            )

            # Send email
            result = await email_service.send_email(
                to_email=email,
                subject=(
                    f"Payment Instructions - Booking #{booking_id}"
                    if booking_id
                    else "Payment Instructions"
                ),
                html_content=html_content,
            )

            return {"success": result, "channel": "email"}

        except Exception as e:
            logger.exception(f"Email instructions failed: {e}")
            return {"success": False, "error": str(e)}

    def _build_email_html(
        self,
        name: str,
        booking_id: int | None,
        amount: Decimal | None,
        payment_methods: list[str],
        include_alternative_payer: bool = False,
    ) -> str:
        """Build HTML email with payment instructions"""

        # Build payment method sections
        methods_html = ""

        if "stripe" in payment_methods:
            methods_html += f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
                <h3 style="color: #635bff; margin: 0 0 10px 0;">💳 Credit/Debit Card (Stripe)</h3>
                <p style="margin: 0 0 10px 0;">Secure online payment - instant confirmation</p>
                <a href="https://myhibachichef.com/pay?booking={booking_id}"
                   style="background: #635bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    Pay with Card
                </a>
                <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">
                    Processing fee: ~3% (included in total)
                </p>
            </div>
            """

        if "zelle" in payment_methods:
            methods_html += f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
                <h3 style="color: #6d1ed4; margin: 0 0 10px 0;">⚡ Zelle (FREE - No Fees)</h3>
                <p style="margin: 0 0 10px 0;">Send via your bank's Zelle to:</p>
                <div style="background: white; padding: 15px; border-radius: 6px; border-left: 4px solid #6d1ed4;">
                    <p style="margin: 0 0 5px 0;"><strong>📱 Phone:</strong> <span style="font-size: 18px; color: #6d1ed4;">{self.zelle_phone}</span></p>
                    <p style="margin: 0;"><strong>📧 Email:</strong> {self.zelle_email}</p>
                </div>
                <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">
                    💡 Add your phone number in the note for faster matching
                </p>
            </div>
            """

        if "venmo" in payment_methods:
            methods_html += f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
                <h3 style="color: #008cff; margin: 0 0 10px 0;">💙 Venmo</h3>
                <p style="margin: 0 0 10px 0;">Send to:</p>
                <div style="background: white; padding: 15px; border-radius: 6px; border-left: 4px solid #008cff;">
                    <p style="margin: 0;"><strong>Username:</strong> <span style="font-size: 18px; color: #008cff;">{self.venmo_username}</span></p>
                </div>
                <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">
                    Processing fee: 3% (included in total)<br>
                    💡 Add your phone number in the note
                </p>
            </div>
            """

        # Alternative payer section
        alt_payer_section = ""
        if include_alternative_payer:
            alt_payer_section = """
            <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin-top: 20px; border-left: 4px solid #ffc107;">
                <h3 style="color: #856404; margin: 0 0 10px 0;">👥 Friend or Family Paying for You?</h3>
                <p style="margin: 0; color: #856404;">
                    No problem! Just let us know who's sending the payment by replying to this email
                    or texting <strong>{self.business_phone}</strong> with their name and phone number.
                    This helps us match the payment to your booking instantly.
                </p>
            </div>
            """

        # Complete HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px 20px;">

                <!-- Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #dc2626; margin: 0 0 10px 0; font-size: 28px;">🔥 {self.business_name}</h1>
                    <p style="color: #666; margin: 0; font-size: 16px;">Payment Instructions</p>
                </div>

                <!-- Greeting -->
                <p style="font-size: 16px; color: #333; margin: 0 0 20px 0;">
                    Hi {name}! 👋
                </p>

                <!-- Payment Details -->
                <div style="background: #fef2f2; padding: 20px; border-radius: 10px; margin-bottom: 30px; border-left: 4px solid #dc2626;">
                    <h2 style="margin: 0 0 15px 0; color: #333; font-size: 20px;">Payment Details</h2>
                    {f'<p style="margin: 0 0 10px 0;"><strong>Booking ID:</strong> #{booking_id}</p>' if booking_id else ''}
                    {f'<p style="margin: 0; font-size: 24px;"><strong>Amount Due:</strong> <span style="color: #dc2626;">${amount:.2f}</span></p>' if amount else ''}
                </div>

                <!-- Payment Methods -->
                <h2 style="color: #333; margin: 0 0 20px 0; font-size: 20px;">Choose Your Payment Method</h2>
                {methods_html}

                {alt_payer_section}

                <!-- Contact Section -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 30px; text-align: center;">
                    <h3 style="margin: 0 0 15px 0; color: #333;">Need Help?</h3>
                    <p style="margin: 0 0 10px 0; font-size: 18px;">
                        <strong>📱 Call/Text:</strong> <a href="tel:{self.business_phone}" style="color: #dc2626; text-decoration: none; font-size: 20px;">{self.business_phone}</a>
                    </p>
                    <p style="margin: 0; font-size: 16px;">
                        <strong>📧 Email:</strong> <a href="mailto:{self.business_email}" style="color: #dc2626; text-decoration: none;">{self.business_email}</a>
                    </p>
                </div>

                <!-- Footer -->
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; text-align: center; color: #666; font-size: 14px;">
                    <p style="margin: 0 0 10px 0;">Thank you for choosing {self.business_name}!</p>
                    <p style="margin: 0;">We can't wait to serve you! 🍜🔥</p>
                </div>

            </div>
        </body>
        </html>
        """

        return html


# Module-level instance
_instructions_service: PaymentInstructionsService | None = None


def get_instructions_service() -> PaymentInstructionsService:
    """Get or create payment instructions service instance"""
    global _instructions_service
    if _instructions_service is None:
        _instructions_service = PaymentInstructionsService()
    return _instructions_service


# Convenience function
async def send_payment_instructions(
    customer_name: str,
    customer_phone: str | None = None,
    customer_email: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Convenience function to send payment instructions"""
    service = get_instructions_service()
    return await service.send_payment_instructions(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        **kwargs,
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        """Test payment instructions"""
        service = PaymentInstructionsService()

        # Test with phone (SMS primary)
        await service.send_payment_instructions(
            customer_name="Suryadi Zhang",
            customer_phone="+12103884155",
            booking_id=123,
            amount=Decimal("550.00"),
            payment_methods=["stripe", "zelle", "venmo"],
        )

    asyncio.run(test())
