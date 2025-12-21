"""
Chef Optimizer Service

Intelligent chef assignment based on location, skills, and preferences.
Provides scoring and optimization for chef-to-booking assignments.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .travel_time_service import TravelTimeService


# Skill requirements by party size
SKILL_THRESHOLDS = {
    "junior": 15,  # Can handle up to 15 guests
    "intermediate": 30,  # Up to 30 guests
    "senior": 50,  # Up to 50 guests
    "executive": 100,  # Large events
}

# Weight factors for scoring
WEIGHT_TRAVEL_TIME = 0.35
WEIGHT_SKILL_MATCH = 0.25
WEIGHT_WORKLOAD_BALANCE = 0.20
WEIGHT_CUSTOMER_HISTORY = 0.15
WEIGHT_PREFERENCE = 0.05


@dataclass
class ChefInfo:
    """Information about a chef"""

    id: UUID
    name: str
    skill_level: str  # junior, intermediate, senior, executive
    max_guests: int
    home_lat: Decimal
    home_lng: Decimal
    current_lat: Optional[Decimal] = None  # Last known location
    current_lng: Optional[Decimal] = None
    is_available: bool = True
    specialties: list[str] = field(default_factory=list)
    rating: float = 5.0


@dataclass
class ChefScore:
    """Scoring result for a chef-booking match"""

    chef_id: UUID
    chef_name: str
    total_score: float
    travel_score: float
    skill_score: float
    workload_score: float
    history_score: float
    travel_time_minutes: Optional[int] = None
    is_preferred: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class AssignmentRecommendation:
    """Final recommendation for chef assignment"""

    booking_id: UUID
    recommended_chef_id: UUID
    recommended_chef_name: str
    confidence_score: float
    all_scores: list[ChefScore]
    reason: str
    is_optimal: bool = True


class ChefOptimizerService:
    """
    Optimizes chef assignments based on multiple factors.

    Scoring factors:
    1. Travel time efficiency (closest chef scores higher)
    2. Skill match (appropriate skill level for party size)
    3. Workload balance (distribute evenly among chefs)
    4. Customer history (same chef for returning customers)
    5. Customer preference (explicit preference gets priority)
    """

    def __init__(
        self,
        session: AsyncSession,
        travel_service: Optional[TravelTimeService] = None,
    ):
        self.session = session
        self.travel_service = travel_service or TravelTimeService(session)
        self._chef_cache: dict[UUID, ChefInfo] = {}

    async def get_optimal_assignment(
        self,
        booking_id: UUID,
        event_date: date,
        event_time: time,
        venue_lat: Decimal,
        venue_lng: Decimal,
        guest_count: int,
        customer_id: Optional[UUID] = None,
        preferred_chef_id: Optional[UUID] = None,
        is_preference_required: bool = False,
    ) -> AssignmentRecommendation:
        """
        Get optimal chef assignment for a booking.

        Args:
            booking_id: The booking being assigned
            event_date: Event date
            event_time: Event start time
            venue_lat: Venue latitude
            venue_lng: Venue longitude
            guest_count: Number of guests
            customer_id: Customer ID for history lookup
            preferred_chef_id: Customer's preferred chef
            is_preference_required: If True, only consider preferred chef

        Returns:
            AssignmentRecommendation with scoring details
        """
        # Get available chefs
        available_chefs = await self._get_available_chefs(event_date, event_time)

        if not available_chefs:
            # No chefs available
            return AssignmentRecommendation(
                booking_id=booking_id,
                recommended_chef_id=UUID("00000000-0000-0000-0000-000000000000"),
                recommended_chef_name="Unassigned",
                confidence_score=0.0,
                all_scores=[],
                reason="No chefs available for this time slot",
                is_optimal=False,
            )

        # If preference is required and chef exists
        if is_preference_required and preferred_chef_id:
            preferred_chef = next((c for c in available_chefs if c.id == preferred_chef_id), None)
            if preferred_chef:
                return AssignmentRecommendation(
                    booking_id=booking_id,
                    recommended_chef_id=preferred_chef.id,
                    recommended_chef_name=preferred_chef.name,
                    confidence_score=1.0,
                    all_scores=[],
                    reason="Customer requested this specific chef",
                    is_optimal=True,
                )
            else:
                # Preferred chef not available - this is a problem
                return AssignmentRecommendation(
                    booking_id=booking_id,
                    recommended_chef_id=UUID("00000000-0000-0000-0000-000000000000"),
                    recommended_chef_name="Unassigned",
                    confidence_score=0.0,
                    all_scores=[],
                    reason="Requested chef is not available for this time slot",
                    is_optimal=False,
                )

        # Score all available chefs
        scores = []
        event_dt = datetime.combine(event_date, event_time)

        for chef in available_chefs:
            score = await self._score_chef(
                chef=chef,
                venue_lat=venue_lat,
                venue_lng=venue_lng,
                event_datetime=event_dt,
                guest_count=guest_count,
                customer_id=customer_id,
                preferred_chef_id=preferred_chef_id,
            )
            scores.append(score)

        # Sort by total score (highest first)
        scores.sort(key=lambda x: x.total_score, reverse=True)

        # Get best match
        best = scores[0]

        # Determine reason
        if best.is_preferred:
            reason = "Customer's preferred chef is available"
        elif best.travel_score > 0.8:
            reason = f"Closest chef with {best.travel_time_minutes} min travel time"
        elif best.skill_score > 0.9:
            reason = f"Best skill match for {guest_count} guest event"
        else:
            reason = "Best overall match considering all factors"

        return AssignmentRecommendation(
            booking_id=booking_id,
            recommended_chef_id=best.chef_id,
            recommended_chef_name=best.chef_name,
            confidence_score=best.total_score,
            all_scores=scores,
            reason=reason,
            is_optimal=True,
        )

    async def _get_available_chefs(
        self,
        event_date: date,
        event_time: time,
    ) -> list[ChefInfo]:
        """
        Get list of chefs available for a specific date/time.

        Checks:
        - Chef is active
        - Not already booked for conflicting time
        - Not on PTO/unavailable
        """
        # Query chef_locations table for active chefs
        from sqlalchemy import text

        query = text(
            """
            SELECT 
                cl.chef_id,
                cl.home_lat,
                cl.home_lng,
                cl.current_lat,
                cl.current_lng,
                cl.is_available,
                cl.skill_level,
                cl.max_party_size
            FROM ops.chef_locations cl
            WHERE cl.is_available = true
              AND cl.chef_id NOT IN (
                  -- Exclude chefs with conflicting bookings
                  SELECT DISTINCT ca.chef_id
                  FROM ops.chef_assignments ca
                  JOIN core.bookings b ON b.id = ca.booking_id
                  WHERE b.event_date = :event_date
                    AND b.status IN ('confirmed', 'pending')
                    AND ABS(EXTRACT(HOUR FROM b.event_time) - :event_hour) < 3
              )
        """
        )

        try:
            result = await self.session.execute(
                query, {"event_date": event_date, "event_hour": event_time.hour}
            )
            rows = result.fetchall()
        except Exception:
            # Table might not exist yet - return mock data
            rows = []

        if not rows:
            # Return mock chefs for development
            return [
                ChefInfo(
                    id=UUID("11111111-1111-1111-1111-111111111111"),
                    name="Chef Marco",
                    skill_level="senior",
                    max_guests=50,
                    home_lat=Decimal("29.7604"),
                    home_lng=Decimal("-95.3698"),
                ),
                ChefInfo(
                    id=UUID("22222222-2222-2222-2222-222222222222"),
                    name="Chef Sofia",
                    skill_level="executive",
                    max_guests=100,
                    home_lat=Decimal("29.7849"),
                    home_lng=Decimal("-95.3969"),
                ),
            ]

        chefs = []
        for row in rows:
            chefs.append(
                ChefInfo(
                    id=row[0],
                    name=f"Chef {row[0][:8]}",  # Placeholder name
                    skill_level=row[6] or "senior",
                    max_guests=row[7] or 50,
                    home_lat=Decimal(str(row[1])),
                    home_lng=Decimal(str(row[2])),
                    current_lat=Decimal(str(row[3])) if row[3] else None,
                    current_lng=Decimal(str(row[4])) if row[4] else None,
                    is_available=row[5],
                )
            )

        return chefs

    async def _score_chef(
        self,
        chef: ChefInfo,
        venue_lat: Decimal,
        venue_lng: Decimal,
        event_datetime: datetime,
        guest_count: int,
        customer_id: Optional[UUID],
        preferred_chef_id: Optional[UUID],
    ) -> ChefScore:
        """
        Calculate comprehensive score for chef-booking match.
        """
        notes = []

        # 1. Travel score (0-1, higher = closer)
        travel_time = await self._calculate_travel_score(chef, venue_lat, venue_lng, event_datetime)
        if travel_time is not None:
            # Normalize: 0 min = 1.0, 60 min = 0.5, 120+ min = 0.0
            travel_score = max(0, 1 - (travel_time / 120))
            notes.append(f"Travel: {travel_time} min")
        else:
            travel_score = 0.5  # Default if unknown
            travel_time = None

        # 2. Skill match score (0-1)
        skill_score = self._calculate_skill_score(chef, guest_count)
        if skill_score < 0.7:
            notes.append(f"Skill level marginal for {guest_count} guests")

        # 3. Workload balance score (0-1)
        workload_score = await self._calculate_workload_score(chef, event_datetime.date())

        # 4. Customer history score (0-1)
        history_score = await self._calculate_history_score(chef.id, customer_id)
        if history_score > 0.5:
            notes.append("Has served this customer before")

        # 5. Preference bonus
        is_preferred = chef.id == preferred_chef_id
        preference_bonus = 1.0 if is_preferred else 0.0
        if is_preferred:
            notes.append("Customer preferred")

        # Calculate weighted total
        total_score = (
            travel_score * WEIGHT_TRAVEL_TIME
            + skill_score * WEIGHT_SKILL_MATCH
            + workload_score * WEIGHT_WORKLOAD_BALANCE
            + history_score * WEIGHT_CUSTOMER_HISTORY
            + preference_bonus * WEIGHT_PREFERENCE
        )

        # Preference gives a significant boost
        if is_preferred:
            total_score = min(1.0, total_score * 1.3)

        return ChefScore(
            chef_id=chef.id,
            chef_name=chef.name,
            total_score=round(total_score, 3),
            travel_score=round(travel_score, 3),
            skill_score=round(skill_score, 3),
            workload_score=round(workload_score, 3),
            history_score=round(history_score, 3),
            travel_time_minutes=travel_time,
            is_preferred=is_preferred,
            notes=notes,
        )

    async def _calculate_travel_score(
        self,
        chef: ChefInfo,
        venue_lat: Decimal,
        venue_lng: Decimal,
        event_datetime: datetime,
    ) -> Optional[int]:
        """Calculate travel time from chef's location to venue."""
        # Use current location if known, otherwise home
        origin_lat = chef.current_lat or chef.home_lat
        origin_lng = chef.current_lng or chef.home_lng

        travel_time = await self.travel_service.get_travel_time(
            float(origin_lat),
            float(origin_lng),
            float(venue_lat),
            float(venue_lng),
            event_datetime,
        )

        return travel_time

    def _calculate_skill_score(
        self,
        chef: ChefInfo,
        guest_count: int,
    ) -> float:
        """
        Score based on chef's skill level matching party size.

        - Under-qualified = low score
        - Over-qualified = acceptable but not optimal
        - Just right = highest score
        """
        # Check if chef can handle this party size
        if guest_count > chef.max_guests:
            return 0.0  # Cannot handle

        # Ideal utilization is 50-90% of max capacity
        utilization = guest_count / chef.max_guests

        if 0.5 <= utilization <= 0.9:
            return 1.0  # Ideal match
        elif utilization < 0.5:
            return 0.7 + (utilization * 0.6)  # Overqualified
        else:
            return 0.9  # Near max capacity

    async def _calculate_workload_score(
        self,
        chef: ChefInfo,
        event_date: date,
    ) -> float:
        """
        Score based on workload distribution.

        Tries to balance work among available chefs.
        """
        # Count bookings for this chef in the week
        from sqlalchemy import text

        week_start = event_date - timedelta(days=event_date.weekday())
        week_end = week_start + timedelta(days=6)

        query = text(
            """
            SELECT COUNT(*)
            FROM ops.chef_assignments ca
            JOIN core.bookings b ON b.id = ca.booking_id
            WHERE ca.chef_id = :chef_id
              AND b.event_date BETWEEN :start AND :end
              AND b.status IN ('confirmed', 'pending')
        """
        )

        try:
            result = await self.session.execute(
                query, {"chef_id": str(chef.id), "start": week_start, "end": week_end}
            )
            weekly_bookings = result.scalar() or 0
        except Exception:
            weekly_bookings = 0

        # Assume 4 bookings/week is full
        max_weekly = 4 * 7 / 4  # ~7 bookings/week max
        return max(0, 1 - (weekly_bookings / max_weekly))

    async def _calculate_history_score(
        self,
        chef_id: UUID,
        customer_id: Optional[UUID],
    ) -> float:
        """
        Score based on previous assignments to this customer.

        Returning customers often prefer the same chef.
        """
        if not customer_id:
            return 0.0

        from sqlalchemy import text

        query = text(
            """
            SELECT COUNT(*)
            FROM ops.chef_assignments ca
            JOIN core.bookings b ON b.id = ca.booking_id
            WHERE ca.chef_id = :chef_id
              AND b.customer_id = :customer_id
              AND b.status = 'completed'
        """
        )

        try:
            result = await self.session.execute(
                query, {"chef_id": str(chef_id), "customer_id": str(customer_id)}
            )
            past_bookings = result.scalar() or 0
        except Exception:
            past_bookings = 0

        # More history = higher score, capped at 1.0
        return min(1.0, past_bookings * 0.25)

    async def get_top_recommendations(
        self,
        booking_id: UUID,
        event_date: date,
        event_time: time,
        venue_lat: Decimal,
        venue_lng: Decimal,
        guest_count: int,
        customer_id: Optional[UUID] = None,
        preferred_chef_id: Optional[UUID] = None,
        limit: int = 3,
    ) -> list[ChefScore]:
        """
        Get top N chef recommendations for station manager to choose from.

        Returns scored list of chefs for manual selection.
        """
        recommendation = await self.get_optimal_assignment(
            booking_id=booking_id,
            event_date=event_date,
            event_time=event_time,
            venue_lat=venue_lat,
            venue_lng=venue_lng,
            guest_count=guest_count,
            customer_id=customer_id,
            preferred_chef_id=preferred_chef_id,
        )

        return recommendation.all_scores[:limit]
