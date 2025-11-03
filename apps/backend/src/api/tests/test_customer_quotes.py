"""
Test pricing service with real customer quotes
Generate quotes for Malia and Debbie with Google Maps integration
"""

import os
import sys

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_src = os.path.join(current_dir, "../..")
sys.path.insert(0, backend_src)

from api.ai.endpoints.services.pricing_service import get_pricing_service


def test_malia_quote():
    """Test Malia's quote: 9 adults, Sonoma, CA"""

    pricing = get_pricing_service(db=None, station_id=None)

    quote = pricing.calculate_party_quote(
        adults=9,
        children=0,
        children_under_5=0,
        upgrades=None,
        addons=None,
        customer_address="Sonoma, CA",
        customer_zipcode="95476",
    )

    if quote["breakdown"].get("travel_info"):
        travel = quote["breakdown"]["travel_info"]
        if travel.get("status") == "success":
            if travel.get("breakdown"):
                travel["breakdown"]
            if travel.get("note"):
                pass
        else:
            pass

    if quote.get("gratuity_guidance"):
        quote["gratuity_guidance"]

    return quote


def test_debbie_quote():
    """Test Debbie's quote: 14 adults + 2 children + 10 filet, Antioch, CA 94509"""

    pricing = get_pricing_service(db=None, station_id=None)

    quote = pricing.calculate_party_quote(
        adults=14,
        children=2,
        children_under_5=0,
        upgrades={"filet_mignon": 10},
        addons=None,
        customer_address="Antioch, CA 94509",
        customer_zipcode="94509",
    )

    if quote["breakdown"].get("upgrades"):
        for _name, _details in quote["breakdown"]["upgrades"].items():
            pass

    if quote["breakdown"].get("travel_info"):
        travel = quote["breakdown"]["travel_info"]
        if travel.get("status") == "success":
            if travel.get("breakdown"):
                travel["breakdown"]
            if travel.get("note"):
                pass
        else:
            pass

    if quote.get("gratuity_guidance"):
        quote["gratuity_guidance"]

    return quote


def test_zip_only_quote():
    """Test quote with ZIP code only (should give polite reminder)"""

    pricing = get_pricing_service(db=None, station_id=None)

    quote = pricing.calculate_party_quote(
        adults=10,
        children=0,
        customer_address=None,  # No full address
        customer_zipcode="94509",  # Only ZIP
    )

    if quote["breakdown"].get("travel_info"):
        travel = quote["breakdown"]["travel_info"]
        if travel.get("distance_miles"):
            pass
        if travel.get("travel_fee") is not None:
            pass
        if travel.get("note"):
            pass

    return quote


if __name__ == "__main__":

    # Test Malia's quote
    malia_quote = test_malia_quote()

    # Test Debbie's quote
    debbie_quote = test_debbie_quote()

    # Test ZIP-only (polite reminder test)
    zip_quote = test_zip_only_quote()
