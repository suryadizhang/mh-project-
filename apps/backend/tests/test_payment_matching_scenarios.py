"""
Test Payment Matching Scenarios
Tests improved name matching (first name, last name, full name)
and flexible OR logic (name OR phone)
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.payment_matcher_service import PaymentMatcher
from src.models.payment import Payment, PaymentStatus
from src.models.booking import Booking


class TestImprovedNameMatching:
    """Test flexible name matching: first name, last name, or full name"""
    
    def test_exact_full_name_match(self, db: Session):
        """Test: Exact full name match gets highest score (+100)"""
        # Setup booking
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        # Sender info from email
        sender_info = {
            "sender_name": "John Smith",  # Exact match
            "amount": 550.00
        }
        
        # Test matching
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        assert match.id == payment.id
        # Score should be 100 (name) + 25 (exact amount) = 125
    
    def test_first_name_only_match(self, db: Session):
        """Test: First name match gets good score (+75)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "John Doe",  # First name matches
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score should be 75 (first name) + 25 (exact amount) = 100
    
    def test_last_name_only_match(self, db: Session):
        """Test: Last name match gets good score (+75)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "Sarah Smith",  # Last name matches
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score should be 75 (last name) + 25 (exact amount) = 100
    
    def test_partial_name_match(self, db: Session):
        """Test: Any word match gets partial score (+50)"""
        booking = Booking(
            customer_name="John Michael Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "Michael Johnson",  # Middle name matches
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score should be 50 (partial) + 25 (exact amount) = 75


class TestPhoneORNameMatching:
    """Test that name OR phone matching works (not both required)"""
    
    def test_phone_match_no_name_match(self, db: Session):
        """Test: Phone matches but name doesn't → Still matches (OR logic)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "Sarah Johnson",  # Name doesn't match
            "sender_phone": "+1 (210) 388-4155",  # Phone DOES match
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score should be 100 (phone) + 25 (exact amount) = 125
    
    def test_name_match_no_phone_match(self, db: Session):
        """Test: Name matches but phone doesn't → Still matches (OR logic)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "John Smith",  # Name DOES match
            "sender_phone": "9165551234",  # Phone doesn't match
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score should be 100 (name) + 25 (exact amount) = 125
    
    def test_both_match_highest_score(self, db: Session):
        """Test: Both name AND phone match → Highest score"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "John Smith",  # Name matches
            "sender_phone": "2103884155",  # Phone matches
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score should be 100 (name) + 100 (phone) + 25 (amount) = 225
    
    def test_neither_match_but_amount_match(self, db: Session):
        """Test: Neither name nor phone match → No match (score < 50)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "Alice Brown",  # Name doesn't match
            "sender_phone": "9165551234",  # Phone doesn't match
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        # Score is only 25 (exact amount) → Below threshold of 50
        assert match is None


class TestAlternativePayerMatching:
    """Test alternative payer matching with improved name logic"""
    
    def test_alternative_payer_exact_name(self, db: Session):
        """Test: Alternative payer exact name match → Highest score (+150)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155",
            metadata={
                "alternative_payer": {
                    "name": "Sarah Johnson",
                    "phone": "9165551234"
                }
            }
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "Sarah Johnson",  # Matches alternative payer
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score: 150 (alt payer exact) + 25 (amount) = 175
    
    def test_alternative_payer_first_name(self, db: Session):
        """Test: Alternative payer first name match → High score (+125)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155",
            metadata={
                "alternative_payer": {
                    "name": "Sarah Johnson",
                    "phone": "9165551234"
                }
            }
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "Sarah Brown",  # First name matches alternative payer
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score: 125 (alt payer first name) + 25 (amount) = 150
    
    def test_alternative_payer_phone(self, db: Session):
        """Test: Alternative payer phone match → High score (+150)"""
        booking = Booking(
            customer_name="John Smith",
            customer_email="john@email.com",
            customer_phone="2103884155",
            metadata={
                "alternative_payer": {
                    "name": "Sarah Johnson",
                    "phone": "9165551234"
                }
            }
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "Unknown Sender",
            "sender_phone": "9165551234",  # Matches alternative payer phone
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score: 150 (alt payer phone) + 25 (amount) = 175


class TestMultipleMatchScoring:
    """Test that highest score wins when multiple bookings match"""
    
    def test_picks_best_match_by_score(self, db: Session):
        """Test: System picks booking with highest score"""
        # Booking 1: Name doesn't match, phone doesn't match
        booking1 = Booking(
            customer_name="Alice Brown",
            customer_phone="9165551111"
        )
        payment1 = Payment(
            booking=booking1,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        # Booking 2: Name matches perfectly
        booking2 = Booking(
            customer_name="John Smith",
            customer_phone="2103884155"
        )
        payment2 = Payment(
            booking=booking2,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_name": "John Smith",  # Matches booking2
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment1, payment2],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        assert match.id == payment2.id  # Should pick booking2


class TestPhoneNormalization:
    """Test phone number normalization handles various formats"""
    
    def test_phone_with_country_code(self, db: Session):
        """Test: +1 (210) 388-4155 matches 2103884155"""
        booking = Booking(
            customer_name="John Smith",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_phone": "+1 (210) 388-4155",  # Various formatting
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
    
    def test_phone_with_dashes(self, db: Session):
        """Test: 210-388-4155 matches 2103884155"""
        booking = Booking(
            customer_name="John Smith",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_phone": "210-388-4155",
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
    
    def test_last_4_digits_match(self, db: Session):
        """Test: Last 4 digits match gives partial score (+40)"""
        booking = Booking(
            customer_name="John Smith",
            customer_phone="2103884155"
        )
        payment = Payment(
            booking=booking,
            total_amount=Decimal("550.00"),
            payment_method="venmo",
            status=PaymentStatus.PENDING
        )
        
        sender_info = {
            "sender_phone": "9165554155",  # Last 4 digits match: 4155
            "amount": 550.00
        }
        
        match = PaymentMatcher._find_best_match_by_sender(
            potential_matches=[payment],
            sender_info=sender_info,
            db=db
        )
        
        assert match is not None
        # Score: 40 (last 4) + 25 (amount) = 65 (above threshold)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
