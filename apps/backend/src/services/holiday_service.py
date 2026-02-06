"""
US Holiday and Event Service
Centralized service for managing US holidays and event planning seasons.

Purpose:
- Track US federal and commercial holidays
- Identify event planning seasons (wedding, graduation, etc.)
- Support marketing campaigns (newsletters, coupons, promotions)
- Provide reusable holiday logic across all features

Used By:
- Coupon reminder system (send holiday-themed messages)
- Newsletter system (holiday campaigns)
- Marketing automation (seasonal promotions)
- Analytics (booking patterns by season)

Author: MH Webapps
Created: November 13, 2025
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HolidayCategory(str, Enum):
    """Categories of holidays and events."""

    FEDERAL = "federal"  # Federal holidays (e.g., Independence Day)
    COMMERCIAL = "commercial"  # Commercial holidays (e.g., Valentine's Day)
    EVENT_SEASON = "event_season"  # Event planning seasons (e.g., wedding season)
    CULTURAL = "cultural"  # Cultural celebrations (e.g., Cinco de Mayo)


class Holiday:
    """Represents a holiday or event with marketing relevance."""

    def __init__(
        self,
        name: str,
        category: HolidayCategory,
        marketing_window_days: int = 14,  # How many days before to start marketing
        description: str = "",
        typical_events: List[str] = None,
    ):
        self.name = name
        self.category = category
        self.marketing_window_days = marketing_window_days
        self.description = description
        self.typical_events = typical_events or []

    def __repr__(self):
        return f"Holiday(name='{self.name}', category='{self.category}')"


class USHolidayService:
    """
    Service for managing US holidays and event planning seasons.

    Features:
    - Accurate date calculation for variable holidays (Thanksgiving, Easter, etc.)
    - Marketing windows (when to start promoting for each holiday)
    - Event season detection (wedding season, graduation season, etc.)
    - Hibachi-relevant events (family gatherings, celebrations)

    Usage Examples:

    # Check current holiday
    service = USHolidayService()
    holiday = service.get_current_holiday()
    if holiday:
        print(f"Current holiday: {holiday.name}")

    # Get upcoming holidays for newsletter
    upcoming = service.get_upcoming_holidays(days=30)
    for holiday, date in upcoming:
        print(f"{holiday.name} on {date}")

    # Check if in marketing window
    if service.is_in_marketing_window(date(2025, 12, 1)):
        print("Start Christmas marketing!")
    """

    def __init__(self):
        """Initialize with US holiday definitions."""
        self.holidays = self._initialize_holidays()

    def _initialize_holidays(self) -> Dict[str, Holiday]:
        """
        Define all tracked US holidays and event seasons.

        Marketing Strategy:
        - Start promoting 2 weeks before major holidays
        - Extend to 4 weeks for event seasons (weddings, graduations)
        - Focus on family gathering events (hibachi is perfect for groups)
        """
        return {
            # === WINTER HOLIDAYS ===
            "new_years": Holiday(
                name="New Year's Day",
                category=HolidayCategory.FEDERAL,
                marketing_window_days=14,
                description="New Year's celebrations and resolutions",
                typical_events=["New Year's Eve parties", "Family gatherings", "Friend reunions"],
            ),
            "super_bowl": Holiday(
                name="Super Bowl Sunday",
                category=HolidayCategory.COMMERCIAL,
                marketing_window_days=14,
                description="America's biggest sports event",
                typical_events=["Watch parties", "Game day gatherings", "Sports celebrations"],
            ),
            "valentines": Holiday(
                name="Valentine's Day",
                category=HolidayCategory.COMMERCIAL,
                marketing_window_days=14,
                description="Romance and date nights",
                typical_events=["Romantic dinners", "Date nights", "Couple celebrations"],
            ),
            # === SPRING HOLIDAYS ===
            "st_patricks": Holiday(
                name="St. Patrick's Day",
                category=HolidayCategory.CULTURAL,
                marketing_window_days=7,
                description="Irish-American celebration",
                typical_events=["Friend gatherings", "Festive parties"],
            ),
            "easter": Holiday(
                name="Easter",
                category=HolidayCategory.FEDERAL,
                marketing_window_days=21,
                description="Spring religious holiday and family time",
                typical_events=["Easter brunches", "Family gatherings", "Spring celebrations"],
            ),
            "cinco_de_mayo": Holiday(
                name="Cinco de Mayo",
                category=HolidayCategory.CULTURAL,
                marketing_window_days=7,
                description="Mexican-American celebration",
                typical_events=["Festive gatherings", "Friend parties"],
            ),
            "mothers_day": Holiday(
                name="Mother's Day",
                category=HolidayCategory.COMMERCIAL,
                marketing_window_days=21,
                description="Honoring mothers - perfect for family events",
                typical_events=["Family brunches", "Mother's Day dinners", "Family celebrations"],
            ),
            "memorial_day": Holiday(
                name="Memorial Day",
                category=HolidayCategory.FEDERAL,
                marketing_window_days=14,
                description="Start of summer - BBQ season kickoff",
                typical_events=["BBQ parties", "Family gatherings", "Summer kickoff events"],
            ),
            # === SUMMER SEASON ===
            "graduation_season": Holiday(
                name="Graduation Season",
                category=HolidayCategory.EVENT_SEASON,
                marketing_window_days=45,  # Start promoting 6 weeks early
                description="High school and college graduations (May-June)",
                typical_events=[
                    "Graduation parties",
                    "Family celebrations",
                    "Achievement celebrations",
                ],
            ),
            "fathers_day": Holiday(
                name="Father's Day",
                category=HolidayCategory.COMMERCIAL,
                marketing_window_days=21,
                description="Honoring fathers - perfect for family events",
                typical_events=["Family dinners", "Father's Day celebrations", "BBQ gatherings"],
            ),
            "independence_day": Holiday(
                name="Independence Day (4th of July)",
                category=HolidayCategory.FEDERAL,
                marketing_window_days=21,
                description="America's birthday - prime party season",
                typical_events=["BBQ parties", "Family gatherings", "Fireworks celebrations"],
            ),
            "summer_wedding_season": Holiday(
                name="Summer Wedding Season",
                category=HolidayCategory.EVENT_SEASON,
                marketing_window_days=60,  # Start promoting 8 weeks early
                description="Peak wedding season (June-August)",
                typical_events=["Wedding receptions", "Rehearsal dinners", "Engagement parties"],
            ),
            # === FALL HOLIDAYS ===
            "labor_day": Holiday(
                name="Labor Day",
                category=HolidayCategory.FEDERAL,
                marketing_window_days=14,
                description="End of summer - last big BBQ weekend",
                typical_events=["BBQ parties", "Family gatherings", "End of summer celebrations"],
            ),
            "back_to_school": Holiday(
                name="Back to School Season",
                category=HolidayCategory.EVENT_SEASON,
                marketing_window_days=21,
                description="August-September school season",
                typical_events=[
                    "Welcome back parties",
                    "Teacher appreciation",
                    "Student gatherings",
                ],
            ),
            "halloween": Holiday(
                name="Halloween",
                category=HolidayCategory.COMMERCIAL,
                marketing_window_days=14,
                description="Costume parties and family fun",
                typical_events=["Halloween parties", "Family gatherings", "Costume events"],
            ),
            "thanksgiving": Holiday(
                name="Thanksgiving",
                category=HolidayCategory.FEDERAL,
                marketing_window_days=21,
                description="America's biggest family gathering holiday",
                typical_events=["Thanksgiving dinners", "Family reunions", "Friendsgiving"],
            ),
            # === WINTER HOLIDAYS (cont.) ===
            "black_friday": Holiday(
                name="Black Friday Weekend",
                category=HolidayCategory.COMMERCIAL,
                marketing_window_days=7,
                description="Holiday shopping kickoff",
                typical_events=["Shopping parties", "Friend gatherings"],
            ),
            "christmas": Holiday(
                name="Christmas",
                category=HolidayCategory.FEDERAL,
                marketing_window_days=45,  # Start Christmas marketing in November
                description="Peak holiday season - office parties, family gatherings",
                typical_events=[
                    "Christmas parties",
                    "Office parties",
                    "Family gatherings",
                    "Holiday celebrations",
                ],
            ),
            "new_years_eve": Holiday(
                name="New Year's Eve",
                category=HolidayCategory.COMMERCIAL,
                marketing_window_days=21,
                description="Year-end celebrations",
                typical_events=["NYE parties", "Friend gatherings", "Celebration dinners"],
            ),
        }

    def get_holiday_date(self, holiday_key: str, year: int) -> Optional[date]:
        """
        Get the actual date for a holiday in a specific year.

        Args:
            holiday_key: Key from self.holidays dict (e.g., "thanksgiving")
            year: Year to calculate date for

        Returns:
            date object, or None if not applicable

        Examples:
            >>> service.get_holiday_date("thanksgiving", 2025)
            datetime.date(2025, 11, 27)  # 4th Thursday of November
        """
        # Fixed date holidays
        fixed_dates = {
            "new_years": (1, 1),
            "valentines": (2, 14),
            "st_patricks": (3, 17),
            "cinco_de_mayo": (5, 5),
            "independence_day": (7, 4),
            "halloween": (10, 31),
            "christmas": (12, 25),
            "new_years_eve": (12, 31),
        }

        if holiday_key in fixed_dates:
            month, day = fixed_dates[holiday_key]
            return date(year, month, day)

        # Variable date holidays
        if holiday_key == "thanksgiving":
            return self._get_thanksgiving(year)

        elif holiday_key == "mothers_day":
            return self._get_nth_weekday(year, 5, 0, 2)  # 2nd Sunday of May

        elif holiday_key == "fathers_day":
            return self._get_nth_weekday(year, 6, 0, 3)  # 3rd Sunday of June

        elif holiday_key == "memorial_day":
            return self._get_last_weekday(year, 5, 0)  # Last Monday of May

        elif holiday_key == "labor_day":
            return self._get_nth_weekday(year, 9, 0, 1)  # 1st Monday of September

        elif holiday_key == "easter":
            return self._get_easter(year)

        elif holiday_key == "super_bowl":
            return self._get_nth_weekday(year, 2, 6, 1)  # 1st Sunday of February

        # Season-based (return start date)
        elif holiday_key == "graduation_season":
            return date(year, 5, 15)  # Mid-May through June

        elif holiday_key == "summer_wedding_season":
            return date(year, 6, 1)  # June through August

        elif holiday_key == "back_to_school":
            return date(year, 8, 15)  # Mid-August

        elif holiday_key == "black_friday":
            # Day after Thanksgiving
            thanksgiving = self._get_thanksgiving(year)
            return thanksgiving + timedelta(days=1)

        return None

    def _get_thanksgiving(self, year: int) -> date:
        """Get Thanksgiving (4th Thursday of November)."""
        return self._get_nth_weekday(year, 11, 3, 4)  # 4th Thursday of November

    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int) -> date:
        """
        Get the nth occurrence of a weekday in a month.

        Args:
            year: Year
            month: Month (1-12)
            weekday: Day of week (0=Monday, 6=Sunday)
            n: Which occurrence (1=first, 2=second, etc.)

        Example:
            _get_nth_weekday(2025, 11, 3, 4) -> 4th Thursday of November 2025
        """
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()

        # Calculate offset to first occurrence
        days_until_weekday = (weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=days_until_weekday)

        # Add weeks to get nth occurrence
        nth_occurrence = first_occurrence + timedelta(weeks=n - 1)

        return nth_occurrence

    def _get_last_weekday(self, year: int, month: int, weekday: int) -> date:
        """Get the last occurrence of a weekday in a month."""
        # Start from last day of month
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        # Walk backwards to find weekday
        while last_day.weekday() != weekday:
            last_day -= timedelta(days=1)

        return last_day

    def _get_easter(self, year: int) -> date:
        """Calculate Easter Sunday using Computus algorithm."""
        # Meeus/Jones/Butcher algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1

        return date(year, month, day)

    def get_current_holiday(
        self, check_date: Optional[date] = None
    ) -> Optional[Tuple[str, Holiday, date]]:
        """
        Get the current holiday or event season.

        Args:
            check_date: Date to check (defaults to today)

        Returns:
            Tuple of (holiday_key, Holiday object, holiday_date) or None

        Example:
            >>> service.get_current_holiday(date(2025, 11, 27))
            ('thanksgiving', Holiday(name='Thanksgiving', ...), date(2025, 11, 27))
        """
        if check_date is None:
            check_date = date.today()

        year = check_date.year

        for key, holiday in self.holidays.items():
            holiday_date = self.get_holiday_date(key, year)
            if holiday_date is None:
                continue

            # Check if within marketing window
            marketing_start = holiday_date - timedelta(days=holiday.marketing_window_days)

            # For seasons, extend the end date
            if holiday.category == HolidayCategory.EVENT_SEASON:
                if key == "graduation_season":
                    marketing_end = date(year, 6, 30)  # Through June
                elif key == "summer_wedding_season":
                    marketing_end = date(year, 8, 31)  # Through August
                elif key == "back_to_school":
                    marketing_end = date(year, 9, 15)  # Mid-September
                else:
                    marketing_end = holiday_date + timedelta(days=30)
            else:
                marketing_end = holiday_date + timedelta(days=3)  # Few days after

            if marketing_start <= check_date <= marketing_end:
                return (key, holiday, holiday_date)

        return None

    def get_upcoming_holidays(
        self,
        days: int = 60,
        from_date: Optional[date] = None,
        categories: Optional[List[HolidayCategory]] = None,
    ) -> List[Tuple[str, Holiday, date]]:
        """
        Get upcoming holidays within specified days.

        Args:
            days: Number of days to look ahead
            from_date: Start date (defaults to today)
            categories: Filter by categories (None = all)

        Returns:
            List of (holiday_key, Holiday object, holiday_date) tuples

        Example:
            >>> service.get_upcoming_holidays(days=90)
            [
                ('christmas', Holiday(...), date(2025, 12, 25)),
                ('new_years', Holiday(...), date(2026, 1, 1)),
            ]
        """
        if from_date is None:
            from_date = date.today()

        end_date = from_date + timedelta(days=days)
        upcoming = []

        # Check current year and next year
        for year in [from_date.year, from_date.year + 1]:
            for key, holiday in self.holidays.items():
                # Filter by category if specified
                if categories and holiday.category not in categories:
                    continue

                holiday_date = self.get_holiday_date(key, year)
                if holiday_date is None:
                    continue

                if from_date <= holiday_date <= end_date:
                    upcoming.append((key, holiday, holiday_date))

        # Sort by date
        upcoming.sort(key=lambda x: x[2])

        return upcoming

    def is_in_marketing_window(
        self, check_date: Optional[date] = None, holiday_key: Optional[str] = None
    ) -> bool:
        """
        Check if date is in marketing window for any holiday.

        Args:
            check_date: Date to check (defaults to today)
            holiday_key: Specific holiday to check (None = any holiday)

        Returns:
            True if in marketing window

        Usage:
            # Check if we should send holiday marketing today
            if service.is_in_marketing_window():
                send_holiday_newsletter()

            # Check if specific holiday is upcoming
            if service.is_in_marketing_window(holiday_key="christmas"):
                send_christmas_promo()
        """
        if check_date is None:
            check_date = date.today()

        if holiday_key:
            # Check specific holiday
            holiday = self.holidays.get(holiday_key)
            if not holiday:
                return False

            holiday_date = self.get_holiday_date(holiday_key, check_date.year)
            if not holiday_date:
                return False

            marketing_start = holiday_date - timedelta(days=holiday.marketing_window_days)
            return marketing_start <= check_date <= holiday_date

        else:
            # Check any holiday
            return self.get_current_holiday(check_date) is not None

    def get_holiday_message_context(
        self, holiday_key: str, check_date: Optional[date] = None
    ) -> Dict[str, any]:
        """
        Get context data for holiday-themed messages.

        Perfect for:
        - SMS messages (coupon reminders)
        - Newsletter content
        - Marketing emails
        - Website banners

        Args:
            holiday_key: Holiday to get context for
            check_date: Date to check (defaults to today)

        Returns:
            Dict with holiday context data

        Example:
            >>> context = service.get_holiday_message_context("thanksgiving")
            >>> print(context)
            {
                'name': 'Thanksgiving',
                'date': date(2025, 11, 27),
                'days_until': 14,
                'typical_events': ['Thanksgiving dinners', 'Family reunions', ...],
                'marketing_angle': 'Perfect for family gatherings',
                'is_peak_season': True
            }
        """
        if check_date is None:
            check_date = date.today()

        holiday = self.holidays.get(holiday_key)
        if not holiday:
            return {}

        holiday_date = self.get_holiday_date(holiday_key, check_date.year)
        if not holiday_date:
            return {}

        days_until = (holiday_date - check_date).days

        # Determine marketing angle based on holiday
        marketing_angles = {
            "thanksgiving": "Perfect for family gatherings and Friendsgiving celebrations",
            "christmas": "Ideal for office parties, family gatherings, and holiday celebrations",
            "new_years_eve": "Ring in the New Year with a memorable hibachi experience",
            "graduation_season": "Celebrate achievements with family and friends",
            "summer_wedding_season": "Perfect for rehearsal dinners and wedding receptions",
            "mothers_day": "Treat Mom to an unforgettable hibachi experience",
            "fathers_day": "Give Dad a memorable dining experience",
            "independence_day": "Celebrate America's birthday with hibachi style",
        }

        return {
            "name": holiday.name,
            "date": holiday_date,
            "days_until": days_until,
            "typical_events": holiday.typical_events,
            "marketing_angle": marketing_angles.get(holiday_key, holiday.description),
            "is_peak_season": holiday.category == HolidayCategory.EVENT_SEASON,
            "category": holiday.category.value,
            "marketing_window_days": holiday.marketing_window_days,
        }

    def get_season_name(self, check_date: Optional[date] = None) -> str:
        """
        Get the current event planning season name.

        Useful for analytics and reporting.

        Returns:
            Season name: "Spring", "Summer Wedding Season", "Fall", "Holiday Season", etc.
        """
        if check_date is None:
            check_date = date.today()

        month = check_date.month

        # Define seasons
        if month in [12, 1, 2]:
            return "Winter / Holiday Season"
        elif month in [3, 4]:
            return "Spring"
        elif month == 5:
            return "Spring / Graduation Season"
        elif month in [6, 7, 8]:
            return "Summer Wedding Season"
        elif month in [9, 10]:
            return "Fall"
        elif month == 11:
            return "Fall / Thanksgiving Season"

        return "General"


# Singleton instance for reuse across application
_holiday_service_instance = None


def get_holiday_service() -> USHolidayService:
    """
    Get singleton instance of holiday service.

    Usage in other services:
        from services.holiday_service import get_holiday_service

        holiday_service = get_holiday_service()
        if holiday_service.is_in_marketing_window():
            # Send holiday promotion
    """
    global _holiday_service_instance
    if _holiday_service_instance is None:
        _holiday_service_instance = USHolidayService()
    return _holiday_service_instance
