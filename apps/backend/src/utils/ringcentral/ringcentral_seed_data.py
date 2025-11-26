"""
RingCentral seed data and testing utilities.
Provides tools for generating test data and validation scenarios.
"""

from datetime import datetime, timedelta, timezone
import random
from typing import Any

from faker import Faker

fake = Faker()


def generate_test_phone_numbers(count: int = 10) -> list[str]:
    """
    Generate test phone numbers for development.

    Args:
        count: Number of phone numbers to generate

    Returns:
        List of formatted phone numbers
    """
    phone_numbers = []

    for _ in range(count):
        # Generate US phone numbers for testing
        area_code = random.choice(["555", "444", "333", "222"])  # Test area codes
        exchange = random.randint(100, 999)
        number = random.randint(1000, 9999)

        phone_numbers.append(f"+1{area_code}{exchange:03d}{number:04d}")

    return phone_numbers


def generate_test_leads_for_sms(count: int = 20) -> list[dict[str, Any]]:
    """
    Generate test leads with SMS-compatible data.

    Args:
        count: Number of leads to generate

    Returns:
        List of lead data dictionaries
    """
    test_phones = generate_test_phone_numbers(count)
    leads = []

    for i, phone in enumerate(test_phones):
        lead_data = {
            "name": fake.name(),
            "phone": phone,
            "email": fake.email(),
            "source": "SMS",
            "status": random.choice(["NEW", "CONTACTED", "QUALIFIED", "PROPOSAL", "WON", "LOST"]),
            "sms_consent": True,
            "notes": f"Test lead {i+1} for SMS integration testing",
            "event_type": random.choice(["wedding", "birthday", "corporate", "anniversary"]),
            "event_date": fake.date_between(start_date="+1d", end_date="+6M"),
            "guest_count": random.randint(10, 200),
            "budget": random.randint(500, 5000),
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
        }
        leads.append(lead_data)

    return leads


def generate_sms_conversation_scenarios() -> list[dict[str, Any]]:
    """
    Generate realistic SMS conversation scenarios for testing.

    Returns:
        List of conversation scenarios
    """
    scenarios = [
        {
            "name": "New Inquiry",
            "description": "Customer asks about hibachi catering",
            "messages": [
                {
                    "direction": "inbound",
                    "text": "Hi! I'm interested in hibachi catering for my wedding. Can you tell me more about your services?",
                    "timestamp_offset": 0,
                },
                {
                    "direction": "outbound",
                    "text": "Hello! Congratulations on your upcoming wedding! We'd love to help make it special. What date are you planning and how many guests?",
                    "timestamp_offset": 300,  # 5 minutes later
                },
                {
                    "direction": "inbound",
                    "text": "Thank you! The wedding is June 15th and we're expecting about 80 guests. What would that cost?",
                    "timestamp_offset": 900,  # 15 minutes later
                },
            ],
        },
        {
            "name": "Booking Confirmation",
            "description": "Customer confirms booking details",
            "messages": [
                {
                    "direction": "inbound",
                    "text": "I'd like to confirm our hibachi catering for this Saturday at 6 PM",
                    "timestamp_offset": 0,
                },
                {
                    "direction": "outbound",
                    "text": "Perfect! We have you confirmed for Saturday 6 PM hibachi catering. Our chef will arrive at 5:30 PM to set up. Looking forward to serving you!",
                    "timestamp_offset": 180,
                },
            ],
        },
        {
            "name": "Menu Questions",
            "description": "Customer asks about menu options",
            "messages": [
                {
                    "direction": "inbound",
                    "text": "What proteins do you offer for hibachi? Any vegetarian options?",
                    "timestamp_offset": 0,
                },
                {
                    "direction": "outbound",
                    "text": "We offer chicken, beef, shrimp, salmon, and scallops. For vegetarians we have tofu hibachi and grilled vegetables. All served with fried rice and vegetables!",
                    "timestamp_offset": 240,
                },
                {
                    "direction": "inbound",
                    "text": "That sounds great! Can we do a mix of chicken and shrimp for our party?",
                    "timestamp_offset": 420,
                },
            ],
        },
        {
            "name": "Pricing Inquiry",
            "description": "Customer asks about pricing",
            "messages": [
                {
                    "direction": "inbound",
                    "text": "What are your rates for hibachi catering for 25 people?",
                    "timestamp_offset": 0,
                },
                {
                    "direction": "outbound",
                    "text": "For 25 people, our hibachi catering starts at $35 per person. This includes chef service, all equipment, protein, rice, vegetables, and cleanup. Would you like a detailed quote?",
                    "timestamp_offset": 300,
                },
            ],
        },
        {
            "name": "Last Minute Booking",
            "description": "Customer needs urgent booking",
            "messages": [
                {
                    "direction": "inbound",
                    "text": "Hi! Do you have any availability for tomorrow evening? It's short notice but we really need hibachi catering for 15 people",
                    "timestamp_offset": 0,
                },
                {
                    "direction": "outbound",
                    "text": "Let me check our schedule! What time were you thinking and what area are you located in?",
                    "timestamp_offset": 120,
                },
                {
                    "direction": "inbound",
                    "text": "Around 7 PM in downtown area. It's for a birthday party!",
                    "timestamp_offset": 300,
                },
            ],
        },
        {
            "name": "Dietary Restrictions",
            "description": "Customer has special dietary needs",
            "messages": [
                {
                    "direction": "inbound",
                    "text": "We have several guests with food allergies. Can you accommodate gluten-free and dairy-free options?",
                    "timestamp_offset": 0,
                },
                {
                    "direction": "outbound",
                    "text": "Absolutely! We regularly accommodate dietary restrictions. We use gluten-free soy sauce and can prepare dairy-free options. Please share all allergies so we can ensure a safe meal for everyone.",
                    "timestamp_offset": 240,
                },
            ],
        },
    ]

    return scenarios


def generate_webhook_test_payloads() -> list[dict[str, Any]]:
    """
    Generate test webhook payloads for development testing.

    Returns:
        List of webhook payload examples
    """
    test_phone = generate_test_phone_numbers(1)[0]
    business_phone = "+15551234567"  # Your business number

    payloads = [
        {
            "name": "Inbound SMS",
            "payload": {
                "uuid": "12345678-1234-1234-1234-123456789012",
                "event": "/restapi/v1.0/account/~/extension/~/message-store",
                "timestamp": "2024-01-15T10:30:00.000Z",
                "subscriptionId": "subscription-123",
                "ownerId": "owner-123",
                "body": {
                    "extensionId": 123456789,
                    "lastUpdated": "2024-01-15T10:30:00.000Z",
                    "changes": [{"type": "SMS", "newCount": 1, "updatedCount": 0}],
                    "messages": [
                        {
                            "id": "msg-123456789",
                            "uri": "/restapi/v1.0/account/~/extension/~/message-store/msg-123456789",
                            "type": "SMS",
                            "from": {"phoneNumber": test_phone, "name": "Test Customer"},
                            "to": [{"phoneNumber": business_phone, "name": "My Hibachi Chef"}],
                            "direction": "Inbound",
                            "subject": "Hi! I'm interested in hibachi catering for my wedding next month. Can you help?",
                            "readStatus": "Unread",
                            "priority": "Normal",
                            "creationTime": "2024-01-15T10:30:00.000Z",
                            "lastModifiedTime": "2024-01-15T10:30:00.000Z",
                        }
                    ],
                },
            },
        },
        {
            "name": "Outbound SMS",
            "payload": {
                "uuid": "12345678-1234-1234-1234-123456789013",
                "event": "/restapi/v1.0/account/~/extension/~/message-store",
                "timestamp": "2024-01-15T10:35:00.000Z",
                "subscriptionId": "subscription-123",
                "ownerId": "owner-123",
                "body": {
                    "extensionId": 123456789,
                    "lastUpdated": "2024-01-15T10:35:00.000Z",
                    "changes": [{"type": "SMS", "newCount": 1, "updatedCount": 0}],
                    "messages": [
                        {
                            "id": "msg-123456790",
                            "uri": "/restapi/v1.0/account/~/extension/~/message-store/msg-123456790",
                            "type": "SMS",
                            "from": {"phoneNumber": business_phone, "name": "My Hibachi Chef"},
                            "to": [{"phoneNumber": test_phone, "name": "Test Customer"}],
                            "direction": "Outbound",
                            "subject": "Hello! Thank you for your interest in our hibachi catering. We'd love to help make your wedding special! What date are you planning and how many guests?",
                            "readStatus": "Read",
                            "priority": "Normal",
                            "creationTime": "2024-01-15T10:35:00.000Z",
                            "lastModifiedTime": "2024-01-15T10:35:00.000Z",
                        }
                    ],
                },
            },
        },
        {
            "name": "Call Event",
            "payload": {
                "uuid": "12345678-1234-1234-1234-123456789014",
                "event": "/restapi/v1.0/account/~/extension/~/call-log",
                "timestamp": "2024-01-15T11:00:00.000Z",
                "subscriptionId": "subscription-124",
                "ownerId": "owner-123",
                "body": {
                    "extensionId": 123456789,
                    "records": [
                        {
                            "id": "call-123456789",
                            "uri": "/restapi/v1.0/account/~/extension/~/call-log/call-123456789",
                            "sessionId": "session-123",
                            "from": {"phoneNumber": test_phone, "name": "Test Customer"},
                            "to": {"phoneNumber": business_phone, "name": "My Hibachi Chef"},
                            "type": "Voice",
                            "direction": "Inbound",
                            "action": "Phone Call",
                            "result": "Accepted",
                            "startTime": "2024-01-15T11:00:00.000Z",
                            "duration": 180,
                            "recording": {
                                "id": "recording-123",
                                "uri": "/restapi/v1.0/account/~/recording/recording-123",
                                "type": "OnDemand",
                                "contentUri": "https://media.ringcentral.com/restapi/v1.0/account/~/recording/recording-123/content",
                            },
                        }
                    ],
                },
            },
        },
    ]

    return payloads


def generate_ai_analysis_test_cases() -> list[dict[str, Any]]:
    """
    Generate test cases for AI message analysis.

    Returns:
        List of test cases with expected AI responses
    """
    test_cases = [
        {
            "message": "Hi! I'm interested in hibachi catering for my wedding next month",
            "expected_intent": "catering_inquiry",
            "expected_urgency": "medium",
            "expected_lead_score": 8,
            "suggested_response": "Congratulations on your upcoming wedding! We'd love to help make it special. What date are you planning and how many guests?",
        },
        {
            "message": "URGENT: Need hibachi catering tomorrow for 50 people!!!",
            "expected_intent": "urgent_booking",
            "expected_urgency": "high",
            "expected_lead_score": 9,
            "suggested_response": "I understand you need catering tomorrow - let me check our availability right away! What time and location are you thinking?",
        },
        {
            "message": "What are your prices?",
            "expected_intent": "pricing_inquiry",
            "expected_urgency": "low",
            "expected_lead_score": 6,
            "suggested_response": "Our hibachi catering starts at $35 per person, including chef service, all equipment, and cleanup. How many guests are you planning for?",
        },
        {
            "message": "Can you do vegetarian hibachi?",
            "expected_intent": "menu_question",
            "expected_urgency": "low",
            "expected_lead_score": 7,
            "suggested_response": "Absolutely! We offer delicious tofu hibachi and grilled vegetables. Our vegetarian options are very popular. When are you thinking of having your event?",
        },
        {
            "message": "I want to cancel my booking for Saturday",
            "expected_intent": "cancellation",
            "expected_urgency": "high",
            "expected_lead_score": 3,
            "suggested_response": "I'm sorry to hear you need to cancel. Let me help you with that right away. Can you confirm the booking details so I can process the cancellation?",
        },
    ]

    return test_cases


def create_test_environment() -> dict[str, Any]:
    """
    Create complete test environment data for RingCentral integration.

    Returns:
        Comprehensive test data package
    """
    return {
        "leads": generate_test_leads_for_sms(20),
        "phone_numbers": generate_test_phone_numbers(30),
        "conversation_scenarios": generate_sms_conversation_scenarios(),
        "webhook_payloads": generate_webhook_test_payloads(),
        "ai_test_cases": generate_ai_analysis_test_cases(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "instructions": {
            "leads": "Use these leads to populate your database for testing",
            "phone_numbers": "Use these for testing SMS sending",
            "conversations": "Simulate these conversation flows",
            "webhooks": "POST these payloads to webhook endpoints for testing",
            "ai_cases": "Test AI analysis against these expected results",
        },
    }


def validate_test_data() -> dict[str, bool]:
    """
    Validate that test data generation is working correctly.

    Returns:
        Validation results for each data type
    """
    try:
        validation = {
            "phone_numbers": len(generate_test_phone_numbers(5)) == 5,
            "leads": len(generate_test_leads_for_sms(3)) == 3,
            "scenarios": len(generate_sms_conversation_scenarios()) > 0,
            "webhooks": len(generate_webhook_test_payloads()) == 3,
            "ai_cases": len(generate_ai_analysis_test_cases()) == 5,
        }

        validation["all_valid"] = all(validation.values())
        return validation

    except Exception as e:
        return {"error": str(e), "all_valid": False}
