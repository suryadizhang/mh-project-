"""
Test coupon restriction and discount cap logic.

Business Rules:
- Minimum order: $550 (business requirement)
- Discount: 10% or $100, whichever is LESS
- Max 1 active coupon per customer
- Max 1 coupon per booking
- Coupon applies to NEXT order

Tests:
1. Max 1 active coupon per customer
2. Max 1 coupon per booking
3. Discount cap: 10% or $100
4. Complete flow: Event A → Coupon → Event B (next order)
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from models.legacy_feedback import CustomerReview, DiscountCoupon
from services.review_service import ReviewService


class TestCouponRestrictions:
    """Test coupon issuance restrictions."""

    @pytest.mark.asyncio
    async def test_one_active_coupon_per_customer(self, db_session):
        """Test: Customer can only have 1 active coupon at a time."""
        service = ReviewService(db_session)
        customer_id = uuid4()
        station_id = uuid4()
        
        # Issue first coupon
        coupon1 = await service._issue_coupon(
            customer_id=customer_id,
            station_id=station_id,
            review_id=uuid4(),
            reason="test_first_coupon",
            discount_percentage=10
        )
        
        assert coupon1 is not None
        assert coupon1.status == "active"
        assert coupon1.times_used == 0
        
        # Check for active coupon
        existing = await service._check_existing_active_coupon(customer_id)
        assert existing is not None
        assert existing.id == coupon1.id
        
        # Try to issue second coupon - should be blocked
        review_id = uuid4()
        review = CustomerReview(
            id=review_id,
            customer_id=customer_id,
            station_id=station_id,
            booking_id=uuid4(),
            rating="could_be_better",
            status="escalated"
        )
        db_session.add(review)
        await db_session.flush()
        
        # Attempt to issue second coupon
        coupon2 = await service.issue_coupon_after_ai_interaction(
            review_id=review_id,
            ai_interaction_notes="Test second coupon",
            discount_percentage=10
        )
        
        # Should be denied
        assert coupon2 is None
        
        # Check metadata has denial reason
        await db_session.refresh(review)
        assert review.metadata is not None
        assert "coupon_denial_reason" in review.metadata
        assert review.metadata["coupon_denial_reason"] == "Customer has active unused coupon"

    @pytest.mark.asyncio
    async def test_one_coupon_per_booking(self, db_session):
        """Test: Each booking can only generate 1 coupon."""
        service = ReviewService(db_session)
        customer_id = uuid4()
        station_id = uuid4()
        booking_id = uuid4()
        
        # Create first review and issue coupon
        review1 = CustomerReview(
            id=uuid4(),
            customer_id=customer_id,
            station_id=station_id,
            booking_id=booking_id,
            rating="could_be_better",
            status="escalated"
        )
        db_session.add(review1)
        await db_session.flush()
        
        coupon1 = await service.issue_coupon_after_ai_interaction(
            review_id=review1.id,
            ai_interaction_notes="First coupon for booking",
            discount_percentage=10
        )
        
        assert coupon1 is not None
        
        # Mark first coupon as used to bypass active coupon check
        coupon1.status = "used"
        coupon1.times_used = 1
        await db_session.commit()
        
        # Create second review for SAME booking
        review2 = CustomerReview(
            id=uuid4(),
            customer_id=customer_id,
            station_id=station_id,
            booking_id=booking_id,  # Same booking!
            rating="could_be_better",
            status="escalated"
        )
        db_session.add(review2)
        await db_session.flush()
        
        # Try to issue second coupon for same booking
        coupon2 = await service.issue_coupon_after_ai_interaction(
            review_id=review2.id,
            ai_interaction_notes="Second coupon for same booking",
            discount_percentage=10
        )
        
        # Should be denied
        assert coupon2 is None
        
        # Check denial reason
        await db_session.refresh(review2)
        assert review2.metadata is not None
        assert "coupon_denial_reason" in review2.metadata
        assert review2.metadata["coupon_denial_reason"] == "Booking already issued coupon"


class TestDiscountCapLogic:
    """Test 10% or $100 maximum discount cap."""

    @pytest.mark.asyncio
    async def test_small_order_10_percent_applied(self, db_session):
        """Test: $600 order → 10% = $60 discount (under $100 cap)."""
        service = ReviewService(db_session)
        customer_id = uuid4()
        
        # Create coupon
        coupon = DiscountCoupon(
            id=uuid4(),
            station_id=uuid4(),
            customer_id=customer_id,
            review_id=uuid4(),
            coupon_code="TEST-60DOLLAR",
            discount_type="percentage",
            discount_value=10,  # 10%
            status="active",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=90),
            minimum_order_cents=55000,  # $550 min (business requirement)
            max_uses=1,
            times_used=0,
            issue_reason="test"
        )
        db_session.add(coupon)
        await db_session.commit()
        
        # Validate coupon on $600 order
        order_total_cents = 60000  # $600
        result = await service.validate_coupon(
            coupon_code="TEST-60DOLLAR",
            customer_id=customer_id,
            order_total_cents=order_total_cents
        )
        
        assert result["valid"] is True
        assert result["coupon"]["discount_cents"] == 6000  # $60 (10% of $600)
        assert result["coupon"]["max_discount_cents"] == 10000  # $100 cap
        assert result["coupon"]["discount_cents"] < result["coupon"]["max_discount_cents"]
        print(f"✅ $600 order: 10% = ${result['coupon']['discount_cents']/100} (under $100 cap)")

    @pytest.mark.asyncio
    async def test_large_order_capped_at_100(self, db_session):
        """Test: $2000 order → 10% = $200, but capped at $100."""
        service = ReviewService(db_session)
        customer_id = uuid4()
        
        # Create coupon
        coupon = DiscountCoupon(
            id=uuid4(),
            station_id=uuid4(),
            customer_id=customer_id,
            review_id=uuid4(),
            coupon_code="TEST-CAPPED",
            discount_type="percentage",
            discount_value=10,  # 10%
            status="active",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=90),
            minimum_order_cents=55000,  # $550 min (business requirement)
            max_uses=1,
            times_used=0,
            issue_reason="test"
        )
        db_session.add(coupon)
        await db_session.commit()
        
        # Validate coupon on $2000 order
        order_total_cents = 200000  # $2000
        result = await service.validate_coupon(
            coupon_code="TEST-CAPPED",
            customer_id=customer_id,
            order_total_cents=order_total_cents
        )
        
        assert result["valid"] is True
        # 10% of $2000 = $200, but should be capped at $100
        assert result["coupon"]["discount_cents"] == 10000  # $100 (capped)
        assert result["coupon"]["max_discount_cents"] == 10000  # $100 cap
        print(f"✅ $2000 order: 10% would be $200, capped at ${result['coupon']['discount_cents']/100}")

    @pytest.mark.asyncio
    async def test_exactly_1000_order(self, db_session):
        """Test: $1000 order → 10% = $100 (exactly at cap)."""
        service = ReviewService(db_session)
        customer_id = uuid4()
        
        # Create coupon
        coupon = DiscountCoupon(
            id=uuid4(),
            station_id=uuid4(),
            customer_id=customer_id,
            review_id=uuid4(),
            coupon_code="TEST-EXACT",
            discount_type="percentage",
            discount_value=10,  # 10%
            status="active",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=90),
            minimum_order_cents=55000,  # \$550 min
            max_uses=1,
            times_used=0,
            issue_reason="test"
        )
        db_session.add(coupon)
        await db_session.commit()
        
        # Validate coupon on $1000 order
        order_total_cents = 100000  # $1000
        result = await service.validate_coupon(
            coupon_code="TEST-EXACT",
            customer_id=customer_id,
            order_total_cents=order_total_cents
        )
        
        assert result["valid"] is True
        assert result["coupon"]["discount_cents"] == 10000  # $100 (10% of $1000)
        assert result["coupon"]["max_discount_cents"] == 10000  # $100 cap
        print(f"✅ $1000 order: 10% = ${result['coupon']['discount_cents']/100} (exactly at cap)")

    @pytest.mark.asyncio
    async def test_minimum_order_requirement(self, db_session):
        """Test: Orders under \$550 cannot use coupon."""
        service = ReviewService(db_session)
        customer_id = uuid4()
        
        # Create coupon
        coupon = DiscountCoupon(
            id=uuid4(),
            station_id=uuid4(),
            customer_id=customer_id,
            review_id=uuid4(),
            coupon_code="TEST-MINORDER",
            discount_type="percentage",
            discount_value=10,
            status="active",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=90),
            minimum_order_cents=55000,  # \$550 minimum
            max_uses=1,
            times_used=0,
            issue_reason="test"
        )
        db_session.add(coupon)
        await db_session.commit()
        
        # Try to use on $40 order (under minimum)
        order_total_cents = 4000  # $40
        result = await service.validate_coupon(
            coupon_code="TEST-MINORDER",
            customer_id=customer_id,
            order_total_cents=order_total_cents
        )
        
        assert result["valid"] is False
        assert "Minimum order" in result["error"]
        print(f"✅ $40 order rejected: {result['error']}")


class TestCouponUsageFlow:
    """Test complete coupon lifecycle: issue → validate → apply."""

    @pytest.mark.asyncio
    async def test_complete_coupon_flow(self, db_session):
        """
        Test complete flow:
        1. Customer books Event A → leaves negative review → gets Coupon
        2. Coupon stored with 10% / $100 cap
        3. Customer books Event B (next order)
        4. Applies coupon at checkout
        5. Gets 10% off (or $100 max)
        6. Coupon marked as used
        7. Cannot use again
        """
        service = ReviewService(db_session)
        customer_id = uuid4()
        station_id = uuid4()
        
        # Step 1: Customer books Event A, leaves negative review
        booking_a_id = uuid4()
        review = CustomerReview(
            id=uuid4(),
            customer_id=customer_id,
            station_id=station_id,
            booking_id=booking_a_id,
            rating="could_be_better",
            status="escalated"
        )
        db_session.add(review)
        await db_session.flush()
        
        # Step 2: AI issues coupon
        coupon = await service.issue_coupon_after_ai_interaction(
            review_id=review.id,
            ai_interaction_notes="Resolved complaint, issued coupon",
            discount_percentage=10
        )
        
        assert coupon is not None
        assert coupon.discount_value == 10  # 10%
        assert coupon.status == "active"
        assert coupon.times_used == 0
        print(f"✅ Step 1-2: Coupon {coupon.coupon_code} issued for Event A review")
        
        # Step 3: Customer books Event B (next order) - $800
        booking_b_id = uuid4()
        next_order_total = 80000  # $800
        
        # Step 4: Validate coupon at checkout
        validation = await service.validate_coupon(
            coupon_code=coupon.coupon_code,
            customer_id=customer_id,
            order_total_cents=next_order_total
        )
        
        assert validation["valid"] is True
        discount_amount = validation["coupon"]["discount_cents"]
        assert discount_amount == 8000  # $80 (10% of $800, under $100 cap)
        print(f"✅ Step 3-4: $800 next order → ${discount_amount/100} discount applied")
        
        # Step 5: Apply coupon to booking
        applied = await service.apply_coupon(
            coupon_code=coupon.coupon_code,
            booking_id=booking_b_id
        )
        
        assert applied is True
        await db_session.refresh(coupon)
        assert coupon.status == "used"
        assert coupon.times_used == 1
        assert coupon.used_in_booking_id == booking_b_id
        print(f"✅ Step 5: Coupon applied to Event B (next order)")
        
        # Step 6: Try to use coupon again - should fail
        validation2 = await service.validate_coupon(
            coupon_code=coupon.coupon_code,
            customer_id=customer_id,
            order_total_cents=50000
        )
        
        assert validation2["valid"] is False
        assert "not valid or expired" in validation2["error"]
        print(f"✅ Step 6: Coupon cannot be reused: {validation2['error']}")


class TestDiscountExamples:
    """Real-world discount calculation examples."""

    @pytest.mark.asyncio
    async def test_discount_examples(self, db_session):
        """Test various order amounts to verify discount logic."""
        service = ReviewService(db_session)
        customer_id = uuid4()
        
        test_cases = [
            # (order_amount, expected_discount, description)
            (100, 10, "$100 order → $10 discount (10%)"),
            (500, 50, "$500 order → $50 discount (10%)"),
            (800, 80, "$800 order → $80 discount (10%)"),
            (1000, 100, "$1000 order → $100 discount (10%, at cap)"),
            (1500, 100, "$1500 order → $100 discount (capped, not $150)"),
            (2000, 100, "$2000 order → $100 discount (capped, not $200)"),
            (5000, 100, "$5000 order → $100 discount (capped, not $500)"),
        ]
        
        for order_dollars, expected_discount_dollars, description in test_cases:
            # Create unique coupon for each test
            coupon_code = f"TEST-{order_dollars}"
            coupon = DiscountCoupon(
                id=uuid4(),
                station_id=uuid4(),
                customer_id=customer_id,
                review_id=uuid4(),
                coupon_code=coupon_code,
                discount_type="percentage",
                discount_value=10,
                status="active",
                valid_from=datetime.now(),
                valid_until=datetime.now() + timedelta(days=90),
                minimum_order_cents=55000,
                max_uses=1,
                times_used=0,
                issue_reason="test"
            )
            db_session.add(coupon)
            await db_session.flush()
            
            # Validate
            result = await service.validate_coupon(
                coupon_code=coupon_code,
                customer_id=customer_id,
                order_total_cents=order_dollars * 100
            )
            
            actual_discount_dollars = result["coupon"]["discount_cents"] / 100
            assert result["valid"] is True
            assert actual_discount_dollars == expected_discount_dollars
            print(f"✅ {description} - Verified!")


if __name__ == "__main__":
    print("Run with: pytest tests/test_coupon_restrictions.py -v")
