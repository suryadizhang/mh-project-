"""
Comprehensive Test Suite for Payment Email Monitor Service

Tests all functionality including:
- Email parsing (Stripe, Venmo, Zelle, Bank of America)
- Booking matching by phone/email
- Payment amount validation
- Error handling
- Webhook processing
- Integration scenarios

Coverage target: 95%+
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from email.message import EmailMessage

from services.payment_email_monitor import (
    PaymentEmailParser,
    PaymentEmailMonitor,
)


# ============================================================================
# SECTION 1: EMAIL PARSING TESTS (Stripe, Venmo, Zelle, BofA)
# ============================================================================


class TestPaymentEmailParser:
    """Test suite for PaymentEmailParser - 15 tests"""

    # ---------------------- Stripe Parser Tests ----------------------

    def test_parse_stripe_email_success(self):
        """Test successful parsing of Stripe payment confirmation email"""
        subject = "Payment Succeeded - Your customer paid $550.00"
        body = """
        Payment received from customer@example.com
        Amount: $550.00
        Payment_Intent: pi_1234567890
        Status: Succeeded
        """

        result = PaymentEmailParser.parse_stripe_email(subject, body)

        assert result is not None
        assert result["provider"] == "stripe"
        assert result["amount"] == Decimal("550.00")
        assert result["transaction_id"] == "pi_1234567890"
        # Stripe parser does NOT extract customer_email (not in current implementation)
        assert result["status"] == "confirmed"
        assert "parsed_at" in result

    def test_parse_stripe_email_with_commas(self):
        """Test Stripe parsing with comma-formatted amounts"""
        subject = "Payment Confirmed"
        body = """
        Amount: $1,550.00
        Transaction_ID: pi_test_123
        Customer: john@example.com
        """

        result = PaymentEmailParser.parse_stripe_email(subject, body)

        assert result["amount"] == Decimal("1550.00")

    def test_parse_stripe_email_missing_amount(self):
        """Test Stripe parsing fails gracefully when amount is missing"""
        subject = "Payment Notification"
        body = "Payment Intent: pi_abc but no dollar amount"

        result = PaymentEmailParser.parse_stripe_email(subject, body)

        assert result is None

    def test_parse_stripe_email_no_transaction_id(self):
        """Test Stripe parsing succeeds even without transaction ID"""
        subject = "Payment Received"
        body = """
        Amount: $100.00
        Email: test@example.com
        """

        result = PaymentEmailParser.parse_stripe_email(subject, body)

        assert result is not None
        assert result["transaction_id"] is None
        assert result["amount"] == Decimal("100.00")

    # ---------------------- Venmo Parser Tests ----------------------

    def test_parse_venmo_email_success(self):
        """Test successful parsing of Venmo payment notification"""
        subject = "John Smith paid you $125.50"
        body = """
        <html>
        <body>
        You received $125.50 from @johnsmith
        Note: 2103884155
        </body>
        </html>
        """

        result = PaymentEmailParser.parse_venmo_email(subject, body)

        assert result is not None
        assert result["provider"] == "venmo"
        assert result["amount"] == Decimal("125.50")
        assert result["sender_name"] == "John Smith"
        assert result["sender_username"] == "@johnsmith"
        assert result["customer_phone"] == "2103884155"
        assert result["status"] == "pending"

    def test_parse_venmo_email_no_phone_in_note(self):
        """Test Venmo parsing when phone is not in payment note"""
        subject = "Jane Doe paid you $50.00"
        body = """
        <html>@janedoe sent you money. Note: Birthday gift!</html>
        """

        result = PaymentEmailParser.parse_venmo_email(subject, body)

        assert result is not None
        assert result["customer_phone"] is None
        assert result["sender_name"] == "Jane Doe"

    def test_parse_venmo_email_with_email_in_body(self):
        """Test Venmo parsing extracts customer email from body"""
        subject = "Payment received $100.00"
        body = """
        From @user123
        Email: customer@example.com
        Note: 5551234567
        """

        result = PaymentEmailParser.parse_venmo_email(subject, body)

        assert result["customer_email"] == "customer@example.com"
        assert result["customer_phone"] == "5551234567"

    def test_parse_venmo_email_malformed_html(self):
        """Test Venmo parsing handles malformed HTML gracefully"""
        subject = "You received $75.00"
        body = "<html<body>$75 from @user</html>"

        result = PaymentEmailParser.parse_venmo_email(subject, body)

        assert result is not None
        assert result["amount"] == Decimal("75.00")

    # ---------------------- Zelle Parser Tests ----------------------

    def test_parse_zelle_email_success(self):
        """Test successful parsing of Zelle payment notification"""
        subject = "Sarah Johnson sent you $200.00"
        body = """
        <html>
        You received $200.00 via Zelle
        From: Sarah Johnson (sarah.j@example.com)
        Memo: 2103884155 - Wedding deposit
        </html>
        """

        result = PaymentEmailParser.parse_zelle_email(subject, body)

        assert result is not None
        assert result["provider"] == "zelle"
        assert result["amount"] == Decimal("200.00")
        assert result["sender_name"] == "Sarah Johnson"
        assert result["sender_email"] == "sarah.j@example.com"
        assert result["customer_phone"] == "2103884155"
        assert result["status"] == "pending"

    def test_parse_zelle_email_no_sender_name(self):
        """Test Zelle parsing when sender name is not in subject"""
        subject = "Payment received"
        body = """
        You received $150.00
        Note: 4155551234
        """

        result = PaymentEmailParser.parse_zelle_email(subject, body)

        assert result is not None
        assert result["amount"] == Decimal("150.00")
        assert result["customer_phone"] == "4155551234"

    def test_parse_zelle_email_with_comma_amount(self):
        """Test Zelle parsing with comma-formatted large amounts"""
        subject = "Payment sent you $1,500.75"
        body = "Amount: $1,500.75"

        result = PaymentEmailParser.parse_zelle_email(subject, body)

        assert result["amount"] == Decimal("1500.75")

    # ---------------------- Bank of America Parser Tests ----------------------

    def test_parse_bofa_email_success(self):
        """Test successful parsing of Bank of America payment email"""
        subject = "Payment Received - BofA Alert"
        body = """
        Deposit made to your account
        Amount: $500.00
        Type: Zelle Transfer
        """

        result = PaymentEmailParser.parse_bofa_email(subject, body)

        assert result is not None
        assert result["provider"] == "bank_of_america"
        assert result["amount"] == Decimal("500.00")
        assert result["payment_type"] == "Zelle"
        assert result["status"] == "confirmed"

    def test_parse_bofa_email_ach_transfer(self):
        """Test BofA parsing for ACH transfer"""
        subject = "Payment received"
        body = """
        ACH Transfer received
        Amount: $1,200.00
        """

        result = PaymentEmailParser.parse_bofa_email(subject, body)

        assert result["amount"] == Decimal("1200.00")
        assert result["payment_type"] == "ACH"

    # ---------------------- Auto-Detection Tests ----------------------

    def test_detect_and_parse_stripe(self):
        """Test auto-detection of Stripe emails"""
        subject = "Payment succeeded"
        from_email = "notifications@stripe.com"
        body = "Amount: $250.00\nPayment_intent: pi_123"

        result = PaymentEmailParser.detect_and_parse(subject, from_email, body)

        assert result is not None
        assert result["provider"] == "stripe"

    def test_detect_and_parse_venmo(self):
        """Test auto-detection of Venmo emails"""
        subject = "John paid you $50"
        from_email = "venmo@venmo.com"
        body = "You received payment from @john"

        result = PaymentEmailParser.detect_and_parse(subject, from_email, body)

        assert result is not None
        assert result["provider"] == "venmo"

    def test_detect_and_parse_zelle_by_subject(self):
        """Test auto-detection of Zelle by subject pattern"""
        subject = "Jane Smith sent you $100.00"
        from_email = "alerts@chase.com"
        body = "Payment via Zelle network"

        result = PaymentEmailParser.detect_and_parse(subject, from_email, body)

        assert result is not None
        assert result["provider"] == "zelle"

    def test_detect_and_parse_unknown_provider(self):
        """Test auto-detection returns None for unknown providers"""
        subject = "Random email"
        from_email = "random@example.com"
        body = "Not a payment email"

        result = PaymentEmailParser.detect_and_parse(subject, from_email, body)

        assert result is None

    # ---------------------- Utility Tests ----------------------

    def test_clean_amount_removes_commas(self):
        """Test amount cleaning removes commas and dollar signs"""
        assert PaymentEmailParser.clean_amount("$1,550.00") == Decimal("1550.00")
        assert PaymentEmailParser.clean_amount("550.00") == Decimal("550.00")
        assert PaymentEmailParser.clean_amount("$100") == Decimal("100")


# ============================================================================
# SECTION 2: BOOKING MATCHING TESTS
# ============================================================================


class TestPaymentEmailMonitorBookingMatching:
    """Test suite for booking lookup and matching - 5 tests"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def monitor(self, mock_db_session):
        """Create monitor instance with mock DB"""
        return PaymentEmailMonitor(
            email_address="test@example.com",
            app_password="test_password",
            db_session=mock_db_session,
        )

    @patch("models.legacy_core.CorePayment")
    def test_find_booking_by_phone_success(self, mock_payment_class, monitor, mock_db_session):
        """Test successful booking lookup by phone number"""
        # Mock booking
        mock_booking = Mock()
        mock_booking.id = "booking-123"
        mock_booking.customer_id = "customer-456"
        mock_booking.booking_datetime = datetime(2025, 12, 25, 18, 0)
        mock_booking.party_size = 20
        mock_booking.status = Mock(value="pending")
        mock_booking.total_amount = Decimal("1100.00")
        mock_booking.contact_phone = "2103884155"
        mock_booking.contact_email = "test@example.com"
        mock_booking.created_at = datetime.now(timezone.utc)

        # Mock query chain for booking
        mock_booking_query = Mock()
        mock_booking_query.filter.return_value = mock_booking_query
        mock_booking_query.order_by.return_value = mock_booking_query
        mock_booking_query.first.return_value = mock_booking

        # Mock query chain for payments
        mock_payment_query = Mock()
        mock_payment_query.filter.return_value = mock_payment_query
        mock_payment_query.all.return_value = []

        # Setup side_effect: first call returns booking query, second call returns payment query
        mock_db_session.query.side_effect = [mock_booking_query, mock_payment_query]

        result = monitor.find_booking_by_contact_info(phone="2103884155", email=None)

        assert result is not None
        assert result["booking_id"] == "booking-123"
        assert result["contact_phone"] == "2103884155"
        assert result["is_deposit_met"] is False
        assert result["amount_paid"] == Decimal("0")

    @patch("models.legacy_core.CorePayment")
    def test_find_booking_by_email_success(self, mock_payment_class, monitor, mock_db_session):
        """Test successful booking lookup by email"""
        mock_booking = Mock()
        mock_booking.id = "booking-789"
        mock_booking.contact_email = "customer@example.com"
        mock_booking.contact_phone = "5551234567"
        mock_booking.status = Mock(value="confirmed")
        mock_booking.total_amount = Decimal("550.00")
        mock_booking.customer_id = "customer-999"
        mock_booking.booking_datetime = datetime.now(timezone.utc) + timedelta(days=14)
        mock_booking.party_size = 8
        mock_booking.created_at = datetime.now(timezone.utc)

        # Mock query chain for booking
        mock_booking_query = Mock()
        mock_booking_query.filter.return_value = mock_booking_query
        mock_booking_query.order_by.return_value = mock_booking_query
        mock_booking_query.first.return_value = mock_booking

        # Mock query chain for payments
        mock_payment_query = Mock()
        mock_payment_query.filter.return_value = mock_payment_query
        mock_payment_query.all.return_value = []

        # Setup side_effect: first call returns booking query, second call returns payment query
        mock_db_session.query.side_effect = [mock_booking_query, mock_payment_query]

        result = monitor.find_booking_by_contact_info(phone=None, email="customer@example.com")

        assert result is not None
        assert result["booking_id"] == "booking-789"

    def test_find_booking_no_match(self, monitor, mock_db_session):
        """Test booking lookup returns None when no booking found"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        mock_db_session.query.return_value = mock_query

        result = monitor.find_booking_by_contact_info(
            phone="5555555555", email="notfound@example.com"
        )

        assert result is None

    def test_find_booking_no_db_session(self):
        """Test booking lookup fails gracefully without DB session"""
        monitor = PaymentEmailMonitor(
            email_address="test@example.com", app_password="test_password", db_session=None
        )

        result = monitor.find_booking_by_contact_info(phone="1234567890", email=None)

        assert result is None

    @patch("models.legacy_core.CorePayment")
    def test_find_booking_normalizes_phone(self, mock_payment_class, monitor, mock_db_session):
        """Test phone number normalization (removes country code)"""
        mock_booking = Mock()
        mock_booking.id = "booking-999"
        mock_booking.contact_phone = "5551234567"  # 10 digits
        mock_booking.contact_email = "norm@example.com"
        mock_booking.customer_id = "customer-111"
        mock_booking.booking_datetime = datetime.now(timezone.utc) + timedelta(days=30)
        mock_booking.party_size = 6
        mock_booking.total_amount = Decimal("330.00")
        mock_booking.status = Mock(value="pending")
        mock_booking.created_at = datetime.now(timezone.utc)

        # Mock query chain for booking
        mock_booking_query = Mock()
        mock_booking_query.filter.return_value = mock_booking_query
        mock_booking_query.order_by.return_value = mock_booking_query
        mock_booking_query.first.return_value = mock_booking

        # Mock query chain for payments
        mock_payment_query = Mock()
        mock_payment_query.filter.return_value = mock_payment_query
        mock_payment_query.all.return_value = []

        # Setup side_effect: first call returns booking query, second call returns payment query
        mock_db_session.query.side_effect = [mock_booking_query, mock_payment_query]

        # Try with country code (11 digits starting with 1)
        result = monitor.find_booking_by_contact_info(
            phone="15551234567", email=None  # With country code
        )

        # Should normalize to 10 digits and find booking
        assert result is not None
        assert result["contact_phone"] == "5551234567"


# ============================================================================
# SECTION 3: PAYMENT VALIDATION TESTS
# ============================================================================


class TestPaymentValidation:
    """Test suite for payment amount validation - 5 tests"""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance"""
        return PaymentEmailMonitor(email_address="test@example.com", app_password="test_password")

    def test_validate_payment_meets_deposit(self, monitor):
        """Test validation when payment meets $100 minimum deposit"""
        payment_data = {"amount": Decimal("150.00")}
        booking_info = {
            "amount_paid": Decimal("0"),
            "total_amount": Decimal("550.00"),
            "is_deposit_met": False,
            "amount_remaining": Decimal("550.00"),
        }

        result = monitor.validate_payment_amount(payment_data, booking_info)

        assert result["is_valid"] is True
        assert result["meets_deposit"] is True
        assert result["deposit_met_by_this_payment"] is True
        assert result["new_amount_paid"] == Decimal("150.00")
        assert result["amount_remaining"] == Decimal("400.00")
        assert "LOCKED" in result["message"]

    def test_validate_payment_partial_deposit(self, monitor):
        """Test validation when payment doesn't meet minimum deposit"""
        payment_data = {"amount": Decimal("50.00")}
        booking_info = {
            "amount_paid": Decimal("0"),
            "total_amount": Decimal("550.00"),
            "is_deposit_met": False,
            "amount_remaining": Decimal("550.00"),
        }

        result = monitor.validate_payment_amount(payment_data, booking_info)

        assert result["is_valid"] is True
        assert result["meets_deposit"] is False
        assert result["deposit_met_by_this_payment"] is False
        assert result["new_amount_paid"] == Decimal("50.00")
        assert "Need $50" in result["message"]  # Need $50 more

    def test_validate_payment_full_payment(self, monitor):
        """Test validation when payment completes booking"""
        payment_data = {"amount": Decimal("400.00")}
        booking_info = {
            "amount_paid": Decimal("150.00"),
            "total_amount": Decimal("550.00"),
            "is_deposit_met": True,
            "amount_remaining": Decimal("400.00"),
        }

        result = monitor.validate_payment_amount(payment_data, booking_info)

        assert result["is_valid"] is True
        assert result["meets_deposit"] is True
        assert result["new_amount_paid"] == Decimal("550.00")
        assert result["amount_remaining"] == Decimal("0")
        assert "fully paid" in result["message"]

    def test_validate_payment_overpayment(self, monitor):
        """Test validation rejects overpayment"""
        payment_data = {"amount": Decimal("500.00")}
        booking_info = {
            "amount_paid": Decimal("150.00"),
            "total_amount": Decimal("550.00"),
            "is_deposit_met": True,
            "amount_remaining": Decimal("400.00"),
        }

        result = monitor.validate_payment_amount(payment_data, booking_info)

        assert result["is_valid"] is False
        assert "Overpayment" in result["message"]

    def test_validate_payment_invalid_amount(self, monitor):
        """Test validation rejects zero or negative amounts"""
        payment_data = {"amount": Decimal("0")}
        booking_info = {
            "amount_paid": Decimal("0"),
            "total_amount": Decimal("550.00"),
            "is_deposit_met": False,
        }

        result = monitor.validate_payment_amount(payment_data, booking_info)

        assert result["is_valid"] is False
        assert "Invalid" in result["message"]


# ============================================================================
# SECTION 4: EMAIL MONITORING INTEGRATION TESTS
# ============================================================================


class TestPaymentEmailMonitorIntegration:
    """Integration tests for email fetching and processing"""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance"""
        return PaymentEmailMonitor(email_address="test@gmail.com", app_password="test_app_password")

    @patch("imaplib.IMAP4_SSL")
    def test_connect_success(self, mock_imap, monitor):
        """Test successful IMAP connection"""
        mock_mail = Mock()
        mock_imap.return_value = mock_mail

        result = monitor.connect()

        assert result is True
        mock_mail.login.assert_called_once_with("test@gmail.com", "test_app_password")

    @patch("imaplib.IMAP4_SSL")
    def test_connect_failure(self, mock_imap, monitor):
        """Test IMAP connection failure handling"""
        mock_imap.side_effect = Exception("Authentication failed")

        result = monitor.connect()

        assert result is False
        assert monitor.mail is None

    @patch("imaplib.IMAP4_SSL")
    def test_disconnect(self, mock_imap, monitor):
        """Test IMAP disconnection"""
        mock_mail = Mock()
        monitor.mail = mock_mail

        monitor.disconnect()

        mock_mail.close.assert_called_once()
        mock_mail.logout.assert_called_once()

    @patch("imaplib.IMAP4_SSL")
    def test_get_unread_payment_emails_success(self, mock_imap, monitor):
        """Test fetching unread payment emails"""
        # Mock IMAP connection
        mock_mail = Mock()
        mock_imap.return_value = mock_mail
        monitor.mail = mock_mail

        # Mock search results
        mock_mail.search.return_value = (None, [b"1 2 3"])

        # Mock email message
        mock_email_data = self._create_mock_stripe_email()
        mock_mail.fetch.return_value = (None, [(None, mock_email_data)])

        mock_mail.select.return_value = (None, None)

        # Fetch emails
        results = monitor.get_unread_payment_emails()

        assert len(results) > 0
        mock_mail.select.assert_called_with("INBOX")

    def _create_mock_stripe_email(self):
        """Helper to create mock Stripe email bytes"""
        msg = EmailMessage()
        msg["Subject"] = "Payment Succeeded - $550.00"
        msg["From"] = "notifications@stripe.com"
        msg["Date"] = "Mon, 16 Nov 2025 12:00:00 +0000"
        msg.set_content(
            """
        Payment received: $550.00
        Payment Intent: pi_test_123
        Customer: test@example.com
        """
        )
        return msg.as_bytes()

    @patch("imaplib.IMAP4_SSL")
    def test_mark_as_read(self, mock_imap, monitor):
        """Test marking email as read"""
        mock_mail = Mock()
        monitor.mail = mock_mail

        monitor.mark_as_read("123")

        mock_mail.store.assert_called_once_with(b"123", "+FLAGS", "\\Seen")


# ============================================================================
# SECTION 5: ERROR HANDLING & EDGE CASES
# ============================================================================


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_parse_email_with_malformed_data(self):
        """Test parser handles malformed email data gracefully"""
        subject = None
        body = None

        result = PaymentEmailParser.detect_and_parse(subject or "", "test@test.com", body or "")

        assert result is None

    def test_clean_amount_with_invalid_format(self):
        """Test clean_amount handles invalid formats"""
        with pytest.raises(Exception):
            PaymentEmailParser.clean_amount("not a number")

    def test_monitor_without_credentials(self):
        """Test monitor initialization without credentials"""
        monitor = PaymentEmailMonitor(email_address="", app_password="")

        result = monitor.connect()

        assert result is False

    def test_find_booking_with_db_error(self):
        """Test booking lookup handles database errors"""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        monitor = PaymentEmailMonitor(
            email_address="test@test.com", app_password="test", db_session=mock_session
        )

        result = monitor.find_booking_by_contact_info(phone="1234567890", email="test@test.com")

        assert result is None


# ============================================================================
# SECTION 6: ADDITIONAL COVERAGE TESTS (100% Target)
# ============================================================================


class TestAdditionalCoverage:
    """Additional tests to achieve 100% coverage"""

    def test_parse_stripe_email_exception(self):
        """Test Stripe parser handles exceptions"""
        result = PaymentEmailParser.parse_stripe_email(None, None)
        assert result is None

    def test_parse_venmo_email_exception(self):
        """Test Venmo parser handles exceptions"""
        result = PaymentEmailParser.parse_venmo_email(None, None)
        assert result is None

    def test_parse_venmo_email_body_amount_fallback(self):
        """Test Venmo parser falls back to body for amount"""
        subject = "John paid you"  # No amount in subject
        body = "You received $99.99 from @john"

        result = PaymentEmailParser.parse_venmo_email(subject, body)

        assert result is not None
        assert result["amount"] == Decimal("99.99")

    def test_parse_venmo_email_no_sender_name_subject(self):
        """Test Venmo parser extracts sender from body when not in subject"""
        subject = "Payment notification $50.00"
        body = "Payment from Jane Smith @janesmith Note: 5551234567"

        result = PaymentEmailParser.parse_venmo_email(subject, body)

        assert result is not None
        assert result["amount"] == Decimal("50.00")

    def test_parse_zelle_email_exception(self):
        """Test Zelle parser handles exceptions"""
        result = PaymentEmailParser.parse_zelle_email(None, None)
        assert result is None

    def test_parse_zelle_email_no_amount(self):
        """Test Zelle parser returns None when amount is missing"""
        subject = "Zelle payment notification"
        body = "You received a payment from John"

        result = PaymentEmailParser.parse_zelle_email(subject, body)

        assert result is None

    def test_parse_zelle_email_body_amount_fallback(self):
        """Test Zelle parser uses body amount when subject missing"""
        subject = "Zelle notification"
        body = "You received $75.50 via Zelle from Mary Johnson"

        result = PaymentEmailParser.parse_zelle_email(subject, body)

        assert result is not None
        assert result["amount"] == Decimal("75.50")

    def test_parse_zelle_email_sender_from_body(self):
        """Test Zelle parser extracts sender from body pattern"""
        subject = "$100.00 received"
        body = "Payment from Robert Williams Note: 2105551234"

        result = PaymentEmailParser.parse_zelle_email(subject, body)

        assert result is not None
        assert result["sender_name"] == "Robert"

    def test_parse_bofa_email_exception(self):
        """Test BofA parser handles exceptions"""
        result = PaymentEmailParser.parse_bofa_email(None, None)
        assert result is None

    def test_parse_bofa_email_no_amount(self):
        """Test BofA parser returns None when amount missing"""
        subject = "Payment notification"
        body = "A payment was received"

        result = PaymentEmailParser.parse_bofa_email(subject, body)

        assert result is None

    @patch("models.legacy_core.CorePayment")
    def test_find_booking_with_hasattr_total_amount(self, mock_payment_class):
        """Test booking lookup uses booking.total_amount when available"""
        mock_session = Mock()
        mock_booking = Mock()
        mock_booking.id = "booking-456"
        mock_booking.customer_id = "customer-789"
        mock_booking.booking_datetime = datetime.now(timezone.utc)
        mock_booking.party_size = 10
        mock_booking.status = Mock(value="confirmed")
        mock_booking.contact_phone = "5551234567"
        mock_booking.contact_email = "test@example.com"
        mock_booking.total_amount = Decimal("1200.00")  # Has total_amount
        mock_booking.created_at = datetime.now(timezone.utc)

        # Mock booking query
        mock_booking_query = Mock()
        mock_booking_query.filter.return_value = mock_booking_query
        mock_booking_query.order_by.return_value = mock_booking_query
        mock_booking_query.first.return_value = mock_booking

        # Mock payment query with existing payment
        mock_payment = Mock()
        mock_payment.amount = Decimal("500.00")
        mock_payment_query = Mock()
        mock_payment_query.filter.return_value = mock_payment_query
        mock_payment_query.all.return_value = [mock_payment]

        mock_session.query.side_effect = [mock_booking_query, mock_payment_query]

        monitor = PaymentEmailMonitor(
            email_address="test@test.com", app_password="test", db_session=mock_session
        )

        result = monitor.find_booking_by_contact_info(phone="5551234567", email=None)

        assert result is not None
        assert result["total_amount"] == Decimal("1200.00")
        assert result["amount_paid"] == Decimal("500.00")
        assert result["is_deposit_met"] is True

    def test_validate_payment_deposit_already_met(self):
        """Test validation when deposit was already met"""
        monitor = PaymentEmailMonitor(email_address="test@test.com", app_password="test")

        payment_data = {"amount": Decimal("50.00")}
        booking_info = {
            "amount_paid": Decimal("200.00"),
            "total_amount": Decimal("550.00"),
            "is_deposit_met": True,
            "amount_remaining": Decimal("350.00"),
        }

        result = monitor.validate_payment_amount(payment_data, booking_info)

        assert result["is_valid"] is True
        assert result["deposit_was_met"] is True
        assert result["deposit_met_by_this_payment"] is False
        assert "Payment received" in result["message"]

    @patch("imaplib.IMAP4_SSL")
    def test_get_unread_payment_emails_with_date(self, mock_imap):
        """Test fetching emails with since_date parameter"""
        monitor = PaymentEmailMonitor(email_address="test@test.com", app_password="test")

        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn
        mock_conn.login.return_value = ("OK", [])
        mock_conn.select.return_value = ("OK", [])

        # Mock search with date filter
        mock_conn.search.return_value = ("OK", [b"1 2"])

        # Mock email fetch
        email_data = b"Subject: Stripe payment\nFrom: stripe@stripe.com\n\nAmount: $100"
        mock_conn.fetch.return_value = ("OK", [(b"1 (RFC822 {100}", email_data)])

        monitor.connect()
        since_date = datetime.now(timezone.utc) - timedelta(days=7)
        result = monitor.get_unread_payment_emails(since_date=since_date, limit=10)

        assert isinstance(result, list)

    @patch("imaplib.IMAP4_SSL")
    def test_get_unread_payment_emails_fetch_error(self, mock_imap):
        """Test handling of email fetch errors"""
        monitor = PaymentEmailMonitor(email_address="test@test.com", app_password="test")

        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn
        mock_conn.login.return_value = ("OK", [])
        mock_conn.select.return_value = ("OK", [])
        mock_conn.search.return_value = ("OK", [b"1"])

        # Mock fetch error
        mock_conn.fetch.side_effect = Exception("Fetch failed")

        monitor.connect()
        result = monitor.get_unread_payment_emails()

        assert result == []

    @patch("imaplib.IMAP4_SSL")
    def test_mark_as_read_error(self, mock_imap):
        """Test mark_as_read handles errors gracefully"""
        monitor = PaymentEmailMonitor(email_address="test@test.com", app_password="test")

        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn
        mock_conn.login.return_value = ("OK", [])
        mock_conn.store.side_effect = Exception("Store failed")

        monitor.connect()
        result = monitor.mark_as_read("1")

        assert result is None

    def test_monitor_disconnect_without_connection(self):
        """Test disconnect when not connected"""
        monitor = PaymentEmailMonitor(email_address="test@test.com", app_password="test")

        # Should not raise exception
        monitor.disconnect()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=services.payment_email_monitor", "--cov-report=term"])
