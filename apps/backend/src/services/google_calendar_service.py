"""
Google Calendar Service for Chef Booking Sync
==============================================

Creates Google Calendar events when chefs are assigned to bookings.
Events are created on the main business calendar and invites are sent
to the assigned chef and station manager.

Configuration:
    - GOOGLE_CALENDAR_ID: The calendar ID (e.g., myhibachichef@gmail.com)
    - Service account credentials via GSM or environment variable

Usage:
    from services.google_calendar_service import create_chef_assignment_event

    # When chef is assigned to a booking:
    await create_chef_assignment_event(
        db=db,
        booking=booking,
        chef_id=chef_id
    )

See: 04-BATCH_DEPLOYMENT.instructions.md for batch context
See: docs/04-DEPLOYMENT/LEGAL_PROTECTION_IMPLEMENTATION.md for chef workflow
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decrypt_pii

if TYPE_CHECKING:
    from db.models.core import Booking
    from db.models.ops import Chef
    from db.models.identity import Station

logger = logging.getLogger(__name__)

# Google Calendar configuration
# GOOGLE_CALENDAR_ID: The calendar to create events on
# - For shared calendars, use the calendar ID (e.g., xyz123@group.calendar.google.com)
# - For primary calendar, use the email address (e.g., myhibachichef@gmail.com)
# Get the ID from: Google Calendar Settings → "My Hibachi" → "Integrate calendar" → "Calendar ID"
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "myhibachichef@gmail.com")

# Service account credentials source priority:
# 1. GOOGLE_SERVICE_ACCOUNT_JSON env var (from GSM via load_config)
# 2. File path fallback for local development
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "gsm-service-account-key.json"
)

# Calendar API scope
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Default event duration in hours
DEFAULT_EVENT_DURATION_HOURS = 3


def _get_calendar_service():
    """
    Get authenticated Google Calendar service using service account.

    Authentication Flow (Priority Order):
    1. GOOGLE_SERVICE_ACCOUNT_JSON env var (GSM - production)
    2. GOOGLE_SERVICE_ACCOUNT_FILE file path (local development fallback)

    Production: Credentials loaded from GSM via load_config() → env var
    Development: Falls back to local file for convenience

    Returns:
        googleapiclient.discovery.Resource: Authenticated Calendar API service

    Raises:
        Exception: If authentication fails
    """
    try:
        credentials = None

        # Priority 1: Load from JSON env var (GSM-sourced in production)
        if GOOGLE_SERVICE_ACCOUNT_JSON:
            logger.debug("📦 Loading Google Calendar credentials from GSM (env var)")
            try:
                sa_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
                credentials = service_account.Credentials.from_service_account_info(
                    sa_info, scopes=SCOPES
                )
                logger.info("✅ Google Calendar credentials loaded from GSM")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse GSM credentials JSON: {e}, falling back to file")

        # Priority 2: Fallback to file-based credentials (local development)
        if credentials is None:
            if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
                logger.error(f"Service account file not found: {GOOGLE_SERVICE_ACCOUNT_FILE}")
                logger.error("💡 For production: Add 'google-calendar-service-account' to GSM")
                logger.error("💡 For local dev: Create gsm-service-account-key.json file")
                raise FileNotFoundError("No Google Calendar credentials available")

            logger.debug(
                f"📁 Loading Google Calendar credentials from file: {GOOGLE_SERVICE_ACCOUNT_FILE}"
            )
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            logger.info("✅ Google Calendar credentials loaded from file (local dev mode)")

        service = build("calendar", "v3", credentials=credentials)
        logger.debug("✅ Google Calendar service initialized successfully")
        return service

    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Calendar service: {e}")
        raise


async def _get_chef_by_id(db: AsyncSession, chef_id: UUID) -> Optional["Chef"]:
    """Fetch chef by ID."""
    from db.models.ops import Chef

    result = await db.execute(select(Chef).where(Chef.id == chef_id))
    return result.scalar_one_or_none()


async def _get_station_by_id(db: AsyncSession, station_id: UUID) -> Optional["Station"]:
    """
    Fetch station by ID.

    Used to get station-specific timezone for calendar events.
    Supports multi-station architecture with different timezones.
    """
    from db.models.identity import Station

    result = await db.execute(select(Station).where(Station.id == station_id))
    return result.scalar_one_or_none()


# Default fallback timezone (Fremont, CA - first station location)
DEFAULT_TIMEZONE = "America/Los_Angeles"


async def _get_event_timezone(
    db: AsyncSession, booking: "Booking", station: Optional["Station"] = None
) -> str:
    """
    Get the timezone for a booking event.

    Priority:
    1. Venue address timezone (most accurate - event happens at venue)
    2. Station timezone (if venue data unavailable)
    3. Default to Pacific timezone (Fremont, CA - first station)

    This approach ensures calendar events display correct times for:
    - Local customers (venue in their timezone)
    - Traveling chefs (event still in venue's timezone)

    Args:
        db: Database session
        booking: The booking with potential venue_address relationship
        station: Optional pre-loaded station (avoids extra query)

    Returns:
        str: IANA timezone string (e.g., "America/Los_Angeles")
    """
    # Priority 1: Try to get timezone from venue address
    if booking.venue_address_id:
        from db.models.address import Address

        # Use existing relationship if loaded, otherwise query
        if hasattr(booking, "venue_address") and booking.venue_address:
            venue_address = booking.venue_address
        else:
            result = await db.execute(select(Address).where(Address.id == booking.venue_address_id))
            venue_address = result.scalar_one_or_none()

        if venue_address:
            # Option 1a: Use explicit timezone field if set
            if venue_address.timezone:
                logger.debug(f"📍 Using venue address timezone: {venue_address.timezone}")
                return venue_address.timezone

            # Option 1b: Derive timezone from lat/lng using tzfpy
            # tzfpy uses (lng, lat) order, NOT (lat, lng)
            if venue_address.lat and venue_address.lng:
                try:
                    from tzfpy import get_tz

                    tz = get_tz(float(venue_address.lng), float(venue_address.lat))
                    if tz:
                        logger.debug(f"🌍 Using lat/lng derived timezone: {tz}")
                        return tz
                except Exception as e:
                    logger.warning(f"⚠️ Failed to derive timezone from lat/lng: {e}")

    # Priority 2: Fall back to station timezone
    if station and station.timezone:
        logger.debug(f"🏢 Using station timezone: {station.timezone}")
        return station.timezone

    # Priority 3: Default to Pacific timezone (Fremont, CA)
    logger.debug(f"🌐 Using default timezone: {DEFAULT_TIMEZONE}")
    return DEFAULT_TIMEZONE


async def _get_station_manager_email(db: AsyncSession, station_id: UUID) -> Optional[str]:
    """
    Get station manager's email for a given station.

    Returns the email of the first user with STATION_MANAGER role for this station.
    """
    from db.models.identity import StationUser, User
    from utils.auth import UserRole

    result = await db.execute(
        select(User.email)
        .join(StationUser, StationUser.user_id == User.id)
        .where(
            StationUser.station_id == station_id,
            StationUser.role == UserRole.STATION_MANAGER.value,
            StationUser.is_active == True,
            User.is_active == True,
        )
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None


def _format_event_description(booking: "Booking", chef: "Chef") -> str:
    """
    Format the event description with booking details.

    Follows the prep summary format from LEGAL_PROTECTION_IMPLEMENTATION.md
    Includes: chef info, venue, menu choices, payment details, tips, allergens.

    Uses encrypted fields with decrypt_pii for customer PII.
    Guest count is party_adults + party_kids.
    """
    allergens = booking.allergen_disclosure or "None disclosed"
    special_requests = booking.special_requests or "None"

    # Decrypt customer info (PII fields are encrypted)
    customer_name = decrypt_pii(booking.customer.name_encrypted) if booking.customer else "TBD"
    customer_phone = decrypt_pii(booking.customer.phone_encrypted) if booking.customer else "N/A"
    customer_email = decrypt_pii(booking.customer.email_encrypted) if booking.customer else "N/A"

    # Decrypt address (encrypted field)
    venue_address = decrypt_pii(booking.address_encrypted) if booking.address_encrypted else "TBD"

    # Calculate guest count (party_adults + party_kids)
    party_adults = booking.party_adults or 0
    party_kids = booking.party_kids or 0
    guest_count = party_adults + party_kids
    guest_display = str(guest_count) if guest_count > 0 else "TBD"

    # Format menu items (JSONB field with protein selections, add-ons, etc.)
    menu_section = _format_menu_items(booking.menu_items, party_adults, party_kids)

    # Format payment details
    deposit_dollars = booking.deposit_due_cents / 100 if booking.deposit_due_cents else 0
    total_dollars = booking.total_due_cents / 100 if booking.total_due_cents else 0
    balance_due = total_dollars - deposit_dollars
    payment_status = booking.status.value if booking.status else "unknown"

    # Format status emoji
    status_emoji = "✅" if payment_status in ("confirmed", "deposit_paid") else "⏳"

    description = f"""📦 MY HIBACHI CHEF ASSIGNMENT

👨‍🍳 CHEF INFO
Name: {chef.first_name} {chef.last_name}
Email: {chef.email}
Phone: {chef.phone or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 VENUE DETAILS
Address: {venue_address}
Adults: {party_adults} | Kids: {party_kids} | Total: {guest_display} guests

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🍽️ MENU CHOICES
{menu_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 PAYMENT DETAILS
{status_emoji} Status: {payment_status.upper()}
💵 Total: ${total_dollars:,.2f}
💳 Deposit: ${deposit_dollars:,.2f}
📋 Balance Due: ${balance_due:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 TIPS INFO
Tips are appreciated and paid directly to the chef after the party.
Suggested: 20-35% of service total
Payment: Cash, Venmo, or Zelle

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ ALLERGENS
{allergens}

📝 SPECIAL REQUESTS
{special_requests}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 CUSTOMER CONTACT
Name: {customer_name}
Phone: {customer_phone}
Email: {customer_email}

🔗 View Booking: https://admin.myhibachichef.com/bookings/{booking.id}

---
This event was automatically created when chef was assigned.
Booking ID: {booking.id}
"""
    return description


def _format_menu_items(menu_items: dict | None, adults: int, kids: int) -> str:
    """
    Format menu items for the calendar event description.

    Expected menu_items structure (JSONB):
    {
        "proteins": {"chicken": 5, "steak": 3, "shrimp": 2},
        "upgrades": {"filet_mignon": 2, "lobster_tail": 1},
        "addons": {"gyoza": 2, "extra_rice": 1}
    }
    """
    if not menu_items:
        total_proteins = (adults + kids) * 2 if adults or kids else 0
        return f"Menu not specified\n(Expecting {total_proteins} protein selections for {adults + kids} guests)"

    lines = []

    # Protein selections
    if "proteins" in menu_items:
        lines.append("BASE PROTEINS:")
        for protein, count in menu_items["proteins"].items():
            protein_display = protein.replace("_", " ").title()
            lines.append(f"  • {protein_display}: {count}")

    # Premium upgrades
    if "upgrades" in menu_items:
        lines.append("\nPREMIUM UPGRADES:")
        for upgrade, count in menu_items["upgrades"].items():
            upgrade_display = upgrade.replace("_", " ").title()
            lines.append(f"  • {upgrade_display}: {count}")

    # Add-ons
    if "addons" in menu_items:
        lines.append("\nADD-ONS:")
        for addon, count in menu_items["addons"].items():
            addon_display = addon.replace("_", " ").title()
            lines.append(f"  • {addon_display}: {count}")

    if not lines:
        return "Menu details pending"

    return "\n".join(lines)


async def create_chef_assignment_event(
    db: AsyncSession, booking: "Booking", chef_id: UUID
) -> Optional[str]:
    """
    Create a Google Calendar event when a chef is assigned to a booking.

    The event is created on the main business calendar (myhibachichef@gmail.com)
    and invites are sent to:
    - The assigned chef (via their email)
    - The station manager (if available)

    Args:
        db: Database session
        booking: The booking being assigned
        chef_id: UUID of the chef being assigned

    Returns:
        str: The created event ID, or None if creation failed

    Example:
        event_id = await create_chef_assignment_event(db, booking, chef_id)
        if event_id:
            logger.info(f"Calendar event created: {event_id}")
    """
    try:
        # Fetch chef details
        chef = await _get_chef_by_id(db, chef_id)
        if not chef:
            logger.error(f"Chef not found: {chef_id}")
            return None

        # Build attendee list
        attendees = []

        # Add chef as attendee
        if chef.email:
            attendees.append(
                {
                    "email": chef.email,
                    "displayName": f"{chef.first_name} {chef.last_name}",
                    "responseStatus": "needsAction",
                }
            )

        # Add station manager as attendee (if available)
        # Also fetch station for timezone fallback
        station = None
        if booking.station_id:
            station = await _get_station_by_id(db, booking.station_id)
            manager_email = await _get_station_manager_email(db, booking.station_id)
            if manager_email:
                attendees.append(
                    {
                        "email": manager_email,
                        "displayName": "Station Manager",
                        "responseStatus": "needsAction",
                    }
                )

        # Get event timezone (venue-based, with station and Pacific fallbacks)
        event_timezone = await _get_event_timezone(db, booking, station)

        # Determine event start/end times
        # Booking model uses 'date' and 'slot' fields
        event_date = booking.date
        event_time = booking.slot  # Booking uses 'slot' for time, not 'time'

        if event_date and event_time:
            # Combine date and time
            start_datetime = datetime.combine(event_date, event_time)
            end_datetime = start_datetime + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)

            start = {"dateTime": start_datetime.isoformat(), "timeZone": event_timezone}
            end = {"dateTime": end_datetime.isoformat(), "timeZone": event_timezone}
        elif event_date:
            # All-day event if no time specified
            start = {"date": event_date.isoformat()}
            end = {"date": (event_date + timedelta(days=1)).isoformat()}
        else:
            logger.warning(f"Booking {booking.id} has no event_date, skipping calendar event")
            return None

        # Build event body
        # Decrypt customer name for display (PII is encrypted)
        customer_name = (
            decrypt_pii(booking.customer.name_encrypted) if booking.customer else "Customer"
        )

        # Decrypt venue address (encrypted field)
        location = (
            decrypt_pii(booking.address_encrypted) if booking.address_encrypted else "Location TBD"
        )

        # Calculate guest count
        guest_count = (booking.party_adults or 0) + (booking.party_kids or 0)
        guest_display = str(guest_count) if guest_count > 0 else "?"

        event_body = {
            "summary": f"🍳 Hibachi Event - {customer_name} ({guest_display} guests)",
            "description": _format_event_description(booking, chef),
            "location": location,
            "start": start,
            "end": end,
            "attendees": attendees,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 48 * 60},  # 48 hours before
                    {"method": "popup", "minutes": 24 * 60},  # 24 hours before
                    {"method": "popup", "minutes": 4 * 60},  # 4 hours before
                ],
            },
            "colorId": "10",  # Green color for assigned events
            "transparency": "opaque",  # Shows as busy
            "status": "confirmed",
        }

        # Create the event
        service = _get_calendar_service()
        event = (
            service.events()
            .insert(
                calendarId=GOOGLE_CALENDAR_ID,
                body=event_body,
                sendUpdates="all",  # Send email invites to attendees
            )
            .execute()
        )

        event_id = event.get("id")
        event_link = event.get("htmlLink")

        logger.info(f"✅ Calendar event created: {event_id} for booking {booking.id}")
        logger.info(f"   📅 Event link: {event_link}")

        return event_id

    except HttpError as e:
        logger.error(f"❌ Google Calendar API error: {e}")
        return None
    except Exception as e:
        logger.exception(f"❌ Failed to create calendar event for booking {booking.id}: {e}")
        return None


async def update_chef_assignment_event(
    db: AsyncSession, booking: "Booking", chef_id: UUID, event_id: str
) -> bool:
    """
    Update an existing Google Calendar event when chef assignment changes.

    Args:
        db: Database session
        booking: The booking being updated
        chef_id: UUID of the new chef
        event_id: The existing calendar event ID

    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        chef = await _get_chef_by_id(db, chef_id)
        if not chef:
            logger.error(f"Chef not found: {chef_id}")
            return False

        # Build updated attendee list
        attendees = []
        if chef.email:
            attendees.append(
                {
                    "email": chef.email,
                    "displayName": f"{chef.first_name} {chef.last_name}",
                    "responseStatus": "needsAction",
                }
            )

        if booking.station_id:
            manager_email = await _get_station_manager_email(db, booking.station_id)
            if manager_email:
                attendees.append({"email": manager_email, "displayName": "Station Manager"})

        # Decrypt customer name for display (PII is encrypted)
        customer_name = (
            decrypt_pii(booking.customer.name_encrypted) if booking.customer else "Customer"
        )

        # Calculate guest count (party_adults + party_kids)
        guest_count = (booking.party_adults or 0) + (booking.party_kids or 0)
        guest_display = str(guest_count) if guest_count > 0 else "?"

        # Update event
        service = _get_calendar_service()
        event = (
            service.events()
            .patch(
                calendarId=GOOGLE_CALENDAR_ID,
                eventId=event_id,
                body={
                    "summary": f"🍳 Hibachi Event - {customer_name} ({guest_display} guests)",
                    "description": _format_event_description(booking, chef),
                    "attendees": attendees,
                },
                sendUpdates="all",
            )
            .execute()
        )

        logger.info(f"✅ Calendar event updated: {event_id} for booking {booking.id}")
        return True

    except HttpError as e:
        logger.error(f"❌ Google Calendar API error updating event {event_id}: {e}")
        return False
    except Exception as e:
        logger.exception(f"❌ Failed to update calendar event {event_id}: {e}")
        return False


async def delete_chef_assignment_event(event_id: str) -> bool:
    """
    Delete a Google Calendar event when chef is unassigned.

    Args:
        event_id: The calendar event ID to delete

    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        service = _get_calendar_service()
        service.events().delete(
            calendarId=GOOGLE_CALENDAR_ID,
            eventId=event_id,
            sendUpdates="all",  # Notify attendees of cancellation
        ).execute()

        logger.info(f"✅ Calendar event deleted: {event_id}")
        return True

    except HttpError as e:
        if e.resp.status == 404:
            logger.warning(f"Calendar event not found (already deleted?): {event_id}")
            return True  # Consider it successful if already gone
        logger.error(f"❌ Google Calendar API error deleting event {event_id}: {e}")
        return False
    except Exception as e:
        logger.exception(f"❌ Failed to delete calendar event {event_id}: {e}")
        return False
