"""
Booking Module Constants
========================

Centralized business constants for booking operations.
All values match the SSoT (Single Source of Truth) system.

See: 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
See: services/business_config_service.py for dynamic values
"""

# ============================================================================
# PRICING CONSTANTS (Fixed amounts in cents for precision)
# ============================================================================

# Fixed deposit amount: $100.00
# NOT a percentage - this is a fixed amount per booking
DEPOSIT_FIXED_CENTS = 100_00  # $100.00

# Party minimum: $550.00 (~10 adults at $55/person)
PARTY_MINIMUM_CENTS = 550_00  # $550.00

# Default adult price: $55.00 (used as fallback if pricing service unavailable)
DEFAULT_ADULT_PRICE_CENTS = 55_00  # $55.00

# Default child price (6-12): $30.00
DEFAULT_CHILD_PRICE_CENTS = 30_00  # $30.00


# ============================================================================
# DEFAULT STATION (Fremont, CA - Main)
# ============================================================================

# Station ID for default assignment
# Format: UUID string
DEFAULT_STATION_ID = "22222222-2222-2222-2222-222222222222"

# Station code (human-readable)
DEFAULT_STATION_CODE = "CA-FREMONT-001"

# Station timezone
DEFAULT_TIMEZONE = "America/Los_Angeles"


# ============================================================================
# BOOKING RULES
# ============================================================================

# Minimum advance booking: 48 hours
MIN_ADVANCE_HOURS = 48

# Deposit payment deadline: 2 hours from booking creation
DEPOSIT_DEADLINE_HOURS = 2

# Internal deadline: 24 hours (for staff to confirm chef assignment)
INTERNAL_DEADLINE_HOURS = 24

# Cancellation refund window: 4 days before event
CANCELLATION_REFUND_DAYS = 4

# Soft delete restore window: 30 days
RESTORE_WINDOW_DAYS = 30


# ============================================================================
# TIME SLOT CONFIGURATION
# ============================================================================

# Available time slots (24-hour format)
TIME_SLOTS = [
    "12:00",  # 12 PM
    "15:00",  # 3 PM
    "18:00",  # 6 PM
    "21:00",  # 9 PM
]

# Business hours
BUSINESS_HOURS_START = 11  # 11:00 AM
BUSINESS_HOURS_END = 22  # 10:00 PM

# Slot duration in minutes
SLOT_DURATION_MINUTES = 180  # 3 hours


# ============================================================================
# TRAVEL FEE CONFIGURATION
# ============================================================================

# Free travel radius in miles
FREE_TRAVEL_MILES = 30

# Per-mile rate after free radius: $2.00
PER_MILE_RATE_CENTS = 200  # $2.00


# ============================================================================
# VALIDATION LIMITS
# ============================================================================

# Guest count limits
MIN_GUESTS = 1
MAX_GUESTS = 50

# Phone number pattern (US format)
US_PHONE_PATTERN = r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"

# Email pattern
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
