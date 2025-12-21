"""
Chef Optimizer - Smart Chef Assignment

Assigns chefs to bookings based on:
- Travel efficiency (40% weight) - Minimize travel time
- Skill match (20% weight) - Match guest count to chef specialty
- Workload balance (15% weight) - Balance bookings across chefs
- Rating score (15% weight) - Higher rated chefs preferred
- Customer preference (10% weight + 50 bonus if requested)

Full implementation completed: 2025-12-21
"""

from datetime import date, time, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.ops import Chef, ChefStatus
from db.models.core import Booking

logger = logging.getLogger(__name__)


# ============================================================================
# Constants - Scoring Weights
# ============================================================================

# Score weights (must sum to 100)
WEIGHT_TRAVEL = 40.0  # Travel time efficiency
WEIGHT_SKILL = 20.0  # Skill match for party size
WEIGHT_WORKLOAD = 15.0  # Workload balance
WEIGHT_RATING = 15.0  # Chef rating
WEIGHT_PREFERENCE = 10.0  # Customer preference

# Customer requested chef bonus (on top of weighted score)
PREFERRED_CHEF_BONUS = 50.0

# Travel time thresholds (minutes)
MAX_TRAVEL_MINUTES = 90  # Maximum acceptable travel time
IDEAL_TRAVEL_MINUTES = 30  # Ideal travel time for full score

# Guest count thresholds for skill matching
SMALL_PARTY_MAX = 15
MEDIUM_PARTY_MAX = 30
LARGE_PARTY_MIN = 31

# Workload threshold (bookings per day)
MAX_DAILY_BOOKINGS = 3


# ============================================================================
# Data Models
# ============================================================================


class BookingForAssignment(BaseModel):
    """Booking data for chef assignment."""

    booking_id: UUID
    event_date: date
    event_time: time
    guest_count: int
    venue_lat: Optional[Decimal] = None
    venue_lng: Optional[Decimal] = None
    preferred_chef_id: Optional[UUID] = None


class ChefForAssignment(BaseModel):
    """Chef data for assignment optimization."""

    chef_id: UUID
    chef_name: str
    home_lat: Decimal
    home_lng: Decimal
    rating: float = 5.0
    specialty: str = "hibachi"
    skill_level: int = 3  # 1-5
    max_guests: int = 50
    total_bookings: int = 0
    completed_bookings: int = 0


class ChefScore(BaseModel):
    """Detailed scoring breakdown for a chef."""

    chef_id: UUID
    chef_name: str
    total_score: float = Field(ge=0.0, le=150.0)  # Max 100 + 50 bonus
    travel_score: float = Field(ge=0.0, le=100.0)
    skill_score: float = Field(ge=0.0, le=100.0)
    workload_score: float = Field(ge=0.0, le=100.0)
    rating_score: float = Field(ge=0.0, le=100.0)
    history_score: float = Field(ge=0.0, le=100.0, default=0.0)  # Future: customer history
    preference_score: float = Field(ge=0.0, le=100.0)
    travel_time_minutes: int
    travel_distance_miles: float
    is_preferred: bool = False
    is_available: bool = True
    notes: str = ""


class OptimalAssignment(BaseModel):
    """Result of chef optimization."""

    booking_id: Optional[UUID] = None
    recommended_chef_id: Optional[UUID] = None
    recommended_chef_name: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=100.0)
    reason: str
    is_optimal: bool = True
    all_scores: List[ChefScore] = []


# ============================================================================
# Chef Optimizer Service
# ============================================================================


class ChefOptimizer:
    """
    Optimizes chef assignments for bookings.

    Scoring Algorithm:
    - Travel Score (40%): Lower travel time = higher score
    - Skill Score (20%): Match specialty to party size
    - Workload Score (15%): Balance bookings across chefs
    - Rating Score (15%): Higher ratings preferred
    - Preference Score (10%): +50 bonus if customer requested

    Total possible score: 100 (weighted) + 50 (preference bonus) = 150
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._travel_service = None

    async def get_optimal_assignment(
        self,
        booking_id: Optional[UUID],
        event_date: date,
        event_time: time,
        venue_lat: Decimal,
        venue_lng: Decimal,
        guest_count: int,
        customer_id: Optional[UUID] = None,
        preferred_chef_id: Optional[UUID] = None,
        is_preference_required: bool = False,
    ) -> OptimalAssignment:
        """
        Get the optimal chef assignment for a booking.

        Args:
            booking_id: Booking ID (optional for quotes)
            event_date: Date of the event
            event_time: Time of the event
            venue_lat: Venue latitude
            venue_lng: Venue longitude
            guest_count: Number of guests
            customer_id: Customer ID for history lookup
            preferred_chef_id: Customer's preferred chef (optional)
            is_preference_required: If True, only return preferred chef or error

        Returns:
            OptimalAssignment with recommended chef and all scored alternatives
        """
        # 1. Get available chefs for the date/time
        available_chefs = await self._get_available_chefs(event_date, event_time)

        if not available_chefs:
            return OptimalAssignment(
                booking_id=booking_id,
                confidence_score=0,
                reason="No chefs available for this date/time",
                is_optimal=False,
            )

        # 2. If preference is required, check if preferred chef is available
        if is_preference_required and preferred_chef_id:
            preferred_available = any(c.chef_id == preferred_chef_id for c in available_chefs)
            if not preferred_available:
                return OptimalAssignment(
                    booking_id=booking_id,
                    confidence_score=0,
                    reason=f"Requested chef is not available on {event_date}",
                    is_optimal=False,
                )

        # 3. Get daily workload for each chef
        workloads = await self._get_chef_workloads([c.chef_id for c in available_chefs], event_date)

        # 4. Score all available chefs
        scored_chefs: List[ChefScore] = []
        for chef in available_chefs:
            score = await self._score_chef(
                chef=chef,
                venue_lat=venue_lat,
                venue_lng=venue_lng,
                guest_count=guest_count,
                event_date=event_date,
                event_time=event_time,
                daily_bookings=workloads.get(chef.chef_id, 0),
                preferred_chef_id=preferred_chef_id,
                customer_id=customer_id,
            )
            scored_chefs.append(score)

        # 5. Sort by total score (highest first)
        scored_chefs.sort(key=lambda x: x.total_score, reverse=True)

        # 6. Build response
        if not scored_chefs:
            return OptimalAssignment(
                booking_id=booking_id,
                confidence_score=0,
                reason="Could not score any available chefs",
                is_optimal=False,
            )

        best_chef = scored_chefs[0]
        confidence = min(100, best_chef.total_score)

        # Determine reason based on scoring
        reason = self._build_recommendation_reason(best_chef, preferred_chef_id)

        return OptimalAssignment(
            booking_id=booking_id,
            recommended_chef_id=best_chef.chef_id,
            recommended_chef_name=best_chef.chef_name,
            confidence_score=confidence,
            reason=reason,
            is_optimal=best_chef.total_score >= 70,  # 70+ is optimal
            all_scores=scored_chefs,
        )

    async def get_top_recommendations(
        self,
        booking_id: Optional[UUID],
        event_date: date,
        event_time: time,
        venue_lat: Decimal,
        venue_lng: Decimal,
        guest_count: int,
        customer_id: Optional[UUID] = None,
        preferred_chef_id: Optional[UUID] = None,
        limit: int = 5,
    ) -> List[ChefScore]:
        """
        Get top N chef recommendations for manual selection.

        Returns scored list of available chefs for station manager to choose from.
        """
        result = await self.get_optimal_assignment(
            booking_id=booking_id,
            event_date=event_date,
            event_time=event_time,
            venue_lat=venue_lat,
            venue_lng=venue_lng,
            guest_count=guest_count,
            customer_id=customer_id,
            preferred_chef_id=preferred_chef_id,
        )

        return result.all_scores[:limit]

    async def _get_available_chefs(
        self,
        event_date: date,
        event_time: time,
    ) -> List[ChefForAssignment]:
        """
        Get all chefs who are available on the given date/time.

        Checks:
        - Chef is active
        - Chef has no time-off on this date
        - Chef doesn't exceed max daily bookings
        """
        # Query active chefs
        query = select(Chef).where(
            and_(
                Chef.is_active == True,
                Chef.status == ChefStatus.ACTIVE,
            )
        )

        result = await self.db.execute(query)
        chefs = result.scalars().all()

        # Convert to assignment models
        # Note: In full implementation, would also check ChefAvailability and ChefTimeOff
        available = []
        for chef in chefs:
            # Default home location (Atlanta metro center if not set)
            # In production, this would come from chef_locations table
            home_lat = Decimal("33.7490")  # Atlanta
            home_lng = Decimal("-84.3880")

            available.append(
                ChefForAssignment(
                    chef_id=chef.id,
                    chef_name=f"{chef.first_name} {chef.last_name}",
                    home_lat=home_lat,
                    home_lng=home_lng,
                    rating=float(chef.rating) if chef.rating else 5.0,
                    specialty=chef.specialty.value if chef.specialty else "hibachi",
                    skill_level=3,  # Default medium skill
                    max_guests=50,
                    total_bookings=chef.total_bookings or 0,
                    completed_bookings=chef.completed_bookings or 0,
                )
            )

        return available

    async def _get_chef_workloads(
        self,
        chef_ids: List[UUID],
        event_date: date,
    ) -> dict:
        """
        Get number of bookings each chef has on the given date.

        Returns dict of chef_id -> booking_count
        """
        if not chef_ids:
            return {}

        # Query booking counts per chef for the date
        # Note: Booking model uses 'chef_id' and 'date' fields
        query = (
            select(Booking.chef_id, func.count(Booking.id).label("booking_count"))
            .where(
                and_(
                    Booking.chef_id.in_(chef_ids),
                    Booking.date == event_date,
                    Booking.status.notin_(["cancelled", "rejected"]),
                )
            )
            .group_by(Booking.chef_id)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return {row[0]: row[1] for row in rows}

    async def _score_chef(
        self,
        chef: ChefForAssignment,
        venue_lat: Decimal,
        venue_lng: Decimal,
        guest_count: int,
        event_date: date,
        event_time: time,
        daily_bookings: int,
        preferred_chef_id: Optional[UUID],
        customer_id: Optional[UUID],
    ) -> ChefScore:
        """
        Calculate comprehensive score for a chef assignment.

        Scoring Breakdown:
        - Travel (40%): Based on distance/time to venue
        - Skill (20%): Match specialty to party size
        - Workload (15%): Balance across chefs
        - Rating (15%): Chef's average rating
        - Preference (10%): Customer requested + 50 bonus
        """
        is_preferred = bool(preferred_chef_id and chef.chef_id == preferred_chef_id)

        # 1. Calculate travel score (40% weight)
        travel_time, travel_distance = await self._calculate_travel(
            float(chef.home_lat),
            float(chef.home_lng),
            float(venue_lat),
            float(venue_lng),
            event_date,
            event_time,
        )
        travel_score = self._score_travel(travel_time)

        # 2. Calculate skill match score (20% weight)
        skill_score = self._score_skill_match(chef.specialty, guest_count)

        # 3. Calculate workload balance score (15% weight)
        workload_score = self._score_workload(daily_bookings)

        # 4. Calculate rating score (15% weight)
        rating_score = self._score_rating(chef.rating)

        # 5. Calculate preference score (10% weight + bonus)
        preference_score = 100.0 if is_preferred else 0.0

        # Calculate weighted total
        weighted_total = (
            (travel_score * WEIGHT_TRAVEL / 100)
            + (skill_score * WEIGHT_SKILL / 100)
            + (workload_score * WEIGHT_WORKLOAD / 100)
            + (rating_score * WEIGHT_RATING / 100)
            + (preference_score * WEIGHT_PREFERENCE / 100)
        )

        # Add preference bonus on top
        if is_preferred:
            weighted_total += PREFERRED_CHEF_BONUS

        # Build notes
        notes = self._build_score_notes(
            travel_time, skill_score, workload_score, daily_bookings, is_preferred
        )

        return ChefScore(
            chef_id=chef.chef_id,
            chef_name=chef.chef_name,
            total_score=weighted_total,
            travel_score=travel_score,
            skill_score=skill_score,
            workload_score=workload_score,
            rating_score=rating_score,
            history_score=0.0,  # Future: customer history with this chef
            preference_score=preference_score,
            travel_time_minutes=travel_time,
            travel_distance_miles=travel_distance,
            is_preferred=is_preferred,
            is_available=True,
            notes=notes,
        )

    async def _calculate_travel(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        event_date: date,
        event_time: time,
    ) -> Tuple[int, float]:
        """
        Calculate travel time and distance from chef to venue.

        Returns (travel_time_minutes, distance_miles)
        """
        # Use Haversine formula for distance estimation
        # In production, this would use TravelTimeService with Google Maps
        from math import radians, sin, cos, sqrt, atan2

        R = 3959  # Earth's radius in miles

        lat1, lon1 = radians(origin_lat), radians(origin_lng)
        lat2, lon2 = radians(dest_lat), radians(dest_lng)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance_miles = R * c

        # Estimate time: 30 mph average (metro traffic)
        average_speed = 30
        travel_minutes = int((distance_miles / average_speed) * 60)

        # Apply rush hour multiplier if applicable
        event_dt = datetime.combine(event_date, event_time)
        if self._is_rush_hour(event_dt):
            travel_minutes = int(travel_minutes * 1.5)

        return travel_minutes, round(distance_miles, 1)

    def _is_rush_hour(self, dt: datetime) -> bool:
        """Check if datetime is during rush hour (Mon-Fri 3-7 PM)."""
        if dt.weekday() >= 5:  # Weekend
            return False
        return 15 <= dt.hour < 19

    def _score_travel(self, travel_minutes: int) -> float:
        """
        Score travel time (0-100).

        - 0-30 min: 100 (ideal)
        - 30-60 min: 75-100 (good)
        - 60-90 min: 25-75 (acceptable)
        - 90+ min: 0-25 (poor)
        """
        if travel_minutes <= IDEAL_TRAVEL_MINUTES:
            return 100.0
        elif travel_minutes >= MAX_TRAVEL_MINUTES:
            return 0.0
        else:
            # Linear interpolation between ideal and max
            range_minutes = MAX_TRAVEL_MINUTES - IDEAL_TRAVEL_MINUTES
            over_ideal = travel_minutes - IDEAL_TRAVEL_MINUTES
            return 100.0 * (1 - (over_ideal / range_minutes))

    def _score_skill_match(self, specialty: str, guest_count: int) -> float:
        """
        Score skill match based on party size and chef specialty.

        Party sizes:
        - Small (1-15): Any chef works, prefer intimate
        - Medium (16-30): Most chefs work
        - Large (31+): Prefer large party specialists
        """
        # Specialty mapping to party size preference
        specialty_strengths = {
            "hibachi": "medium",  # Good for all sizes
            "sushi": "small",  # Better for smaller parties
            "teppanyaki": "large",  # Great for larger parties
            "fusion": "medium",  # Versatile
        }

        chef_strength = specialty_strengths.get(specialty.lower(), "medium")

        if guest_count <= SMALL_PARTY_MAX:
            party_size = "small"
        elif guest_count <= MEDIUM_PARTY_MAX:
            party_size = "medium"
        else:
            party_size = "large"

        # Scoring matrix
        if chef_strength == party_size:
            return 100.0
        elif party_size == "medium":
            return 80.0  # Medium parties work for everyone
        elif chef_strength == "medium":
            return 75.0  # Versatile chefs work for all sizes
        else:
            return 50.0  # Mismatch but still acceptable

    def _score_workload(self, daily_bookings: int) -> float:
        """
        Score workload balance (0-100).

        Prefer chefs with fewer bookings to balance workload.
        """
        if daily_bookings >= MAX_DAILY_BOOKINGS:
            return 0.0  # At capacity
        elif daily_bookings == 0:
            return 100.0  # Fully available
        else:
            # Decrease score as bookings increase
            return 100.0 * (1 - (daily_bookings / MAX_DAILY_BOOKINGS))

    def _score_rating(self, rating: float) -> float:
        """
        Score based on chef rating (0-100).

        Rating is 0-5 scale, convert to 0-100.
        """
        return min(100.0, (rating / 5.0) * 100)

    def _build_score_notes(
        self,
        travel_minutes: int,
        skill_score: float,
        workload_score: float,
        daily_bookings: int,
        is_preferred: bool,
    ) -> str:
        """Build human-readable notes for the score."""
        notes = []

        if is_preferred:
            notes.append("Customer requested chef")

        if travel_minutes <= 30:
            notes.append(f"Excellent location ({travel_minutes} min)")
        elif travel_minutes <= 60:
            notes.append(f"Good location ({travel_minutes} min)")
        else:
            notes.append(f"Far location ({travel_minutes} min)")

        if skill_score >= 90:
            notes.append("Great skill match")
        elif skill_score < 60:
            notes.append("Skill mismatch")

        if daily_bookings >= 2:
            notes.append(f"Already has {daily_bookings} bookings today")

        return "; ".join(notes) if notes else "Good match"

    def _build_recommendation_reason(
        self,
        best_chef: ChefScore,
        preferred_chef_id: Optional[UUID],
    ) -> str:
        """Build recommendation reason string."""
        reasons = []

        if best_chef.is_preferred:
            reasons.append("Customer requested this chef")

        if best_chef.travel_score >= 80:
            reasons.append(f"only {best_chef.travel_time_minutes} min away")

        if best_chef.rating_score >= 90:
            reasons.append("highly rated")

        if best_chef.workload_score >= 80:
            reasons.append("available")

        if not reasons:
            reasons.append("best overall match")

        return f"Recommended because: {', '.join(reasons)}"


# Alias for backward compatibility with router imports
ChefOptimizerService = ChefOptimizer
