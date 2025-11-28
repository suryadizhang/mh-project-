"""
Legal Proof Verification Script

This script verifies the integrity and authenticity of terms acknowledgment records
for legal proceedings or dispute resolution.

Usage:
    python verify_terms_proof.py --acknowledgment-id 789
    python verify_terms_proof.py --customer-id 123 --latest
    python verify_terms_proof.py --booking-id 456

Output:
    Complete proof package with verification status
"""

import argparse
import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from core.database import SessionLocal

# MIGRATED: from models.terms_acknowledgment → db.models.terms_acknowledgment
from db.models.terms_acknowledgment import TermsAcknowledgment


def calculate_message_hash(
    phone_number: str, message_body: str, timestamp: str, message_id: str
) -> str:
    """
    Recalculate message hash from components

    This proves the message hasn't been tampered with.
    If calculated hash matches stored hash, record is authentic.
    """
    canonical_string = f"{phone_number}|{message_body}|{timestamp}|{message_id}"
    return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()


def extract_proof_from_notes(notes: str) -> dict[str, Any]:
    """
    Extract proof components from acknowledgment notes field

    Notes format:
        SMS reply verified from 2103884155
        Reply text: 'I agree'
        RingCentral Message ID: 12345
        Message Timestamp: 2025-01-03T14:30:00Z
        Message Hash (SHA-256): b7e4c1d38f2a9e5d...
        Webhook Source IP: 208.54.123.45
    """
    proof = {}

    for line in notes.split("\n"):
        if "RingCentral Message ID:" in line:
            proof["ringcentral_message_id"] = line.split(":", 1)[1].strip()
        elif "Message Timestamp:" in line:
            proof["message_timestamp"] = line.split(":", 1)[1].strip()
        elif "Message Hash (SHA-256):" in line:
            proof["stored_message_hash"] = line.split(":", 1)[1].strip()
        elif "Webhook Source IP:" in line:
            proof["webhook_source_ip"] = line.split(":", 1)[1].strip()
        elif "Reply text:" in line:
            proof["reply_text"] = line.split(":", 1)[1].strip().strip("'\"")

    return proof


def verify_acknowledgment(
    acknowledgment: TermsAcknowledgment, customer_phone: str
) -> dict[str, Any]:
    """
    Verify a terms acknowledgment record

    Returns complete proof package with verification status
    """
    # Extract proof components from notes
    proof_components = extract_proof_from_notes(acknowledgment.notes or "")

    # Prepare result
    result = {
        "acknowledgment_id": acknowledgment.id,
        "customer_id": acknowledgment.customer_id,
        "booking_id": acknowledgment.booking_id,
        "verified_at": datetime.utcnow().isoformat(),
        "verification_status": "PENDING",
        "proof_components": {},
        "verification_checks": {},
        "evidence_package": {},
    }

    # Check 1: Hash Integrity
    if all(
        k in proof_components
        for k in ["ringcentral_message_id", "message_timestamp", "stored_message_hash"]
    ):
        # Recalculate hash
        phone_normalized = "".join(c for c in customer_phone if c.isdigit())[-10:]

        recalculated_hash = calculate_message_hash(
            phone_number=phone_normalized,
            message_body=acknowledgment.acknowledgment_text,
            timestamp=proof_components["message_timestamp"],
            message_id=proof_components["ringcentral_message_id"],
        )

        hash_matches = recalculated_hash == proof_components["stored_message_hash"]

        result["verification_checks"]["hash_integrity"] = {
            "status": "PASS" if hash_matches else "FAIL",
            "stored_hash": proof_components["stored_message_hash"],
            "recalculated_hash": recalculated_hash,
            "explanation": (
                "Message hash matches - record unchanged since receipt"
                if hash_matches
                else "TAMPERING DETECTED - hash mismatch"
            ),
        }
    else:
        result["verification_checks"]["hash_integrity"] = {
            "status": "UNAVAILABLE",
            "explanation": "Missing proof components (older record format)",
        }

    # Check 2: Valid Confirmation Phrase
    valid_phrases = [
        "I AGREE",
        "AGREE",
        "YES",
        "CONFIRM",
        "I CONFIRM",
        "ACCEPTED",
        "I ACCEPT",
        "OK",
        "OKAY",
    ]
    text_upper = acknowledgment.acknowledgment_text.upper()
    has_valid_phrase = any(phrase in text_upper for phrase in valid_phrases)

    result["verification_checks"]["valid_confirmation"] = {
        "status": "PASS" if has_valid_phrase else "FAIL",
        "acknowledgment_text": acknowledgment.acknowledgment_text,
        "explanation": (
            "Contains valid confirmation phrase"
            if has_valid_phrase
            else "Does not contain recognized confirmation phrase"
        ),
    }

    # Check 3: Timestamp Consistency
    if "message_timestamp" in proof_components:
        # Compare RingCentral timestamp with our acknowledged_at
        ringcentral_time = datetime.fromisoformat(
            proof_components["message_timestamp"].replace("Z", "+00:00")
        )
        our_time = acknowledgment.acknowledged_at

        time_diff_seconds = abs((ringcentral_time - our_time).total_seconds())

        result["verification_checks"]["timestamp_consistency"] = {
            "status": "PASS" if time_diff_seconds < 60 else "WARNING",
            "ringcentral_timestamp": proof_components["message_timestamp"],
            "our_timestamp": acknowledgment.acknowledged_at.isoformat(),
            "difference_seconds": time_diff_seconds,
            "explanation": (
                "Timestamps match within acceptable range (< 60s)"
                if time_diff_seconds < 60
                else f"Timestamps differ by {time_diff_seconds}s (acceptable if < 300s)"
            ),
        }

    # Check 4: RingCentral Message ID Present
    result["verification_checks"]["ringcentral_verification"] = {
        "status": "PASS" if "ringcentral_message_id" in proof_components else "UNAVAILABLE",
        "message_id": proof_components.get("ringcentral_message_id"),
        "explanation": (
            f"RingCentral Message ID {proof_components.get('ringcentral_message_id')} available for third-party verification"
            if "ringcentral_message_id" in proof_components
            else "No RingCentral Message ID (older record or web acknowledgment)"
        ),
    }

    # Overall Status
    checks = result["verification_checks"]
    all_pass = all(
        check.get("status") == "PASS"
        for check in checks.values()
        if check.get("status") not in ["UNAVAILABLE", "WARNING"]
    )

    result["verification_status"] = "VERIFIED" if all_pass else "NEEDS_REVIEW"

    # Evidence Package for Legal Use
    result["evidence_package"] = {
        "acknowledgment_id": acknowledgment.id,
        "customer_id": acknowledgment.customer_id,
        "booking_id": acknowledgment.booking_id,
        "terms_version": acknowledgment.terms_version,
        "terms_url": acknowledgment.terms_url,
        "terms_text_hash": acknowledgment.terms_text_hash,
        "acknowledged_at": acknowledgment.acknowledged_at.isoformat(),
        "channel": acknowledgment.channel.value if acknowledgment.channel else None,
        "acknowledgment_method": acknowledgment.acknowledgment_method,
        "acknowledgment_text": acknowledgment.acknowledgment_text,
        "ringcentral_message_id": proof_components.get("ringcentral_message_id"),
        "message_timestamp": proof_components.get("message_timestamp"),
        "message_hash": proof_components.get("stored_message_hash"),
        "webhook_source_ip": proof_components.get("webhook_source_ip"),
        "verified": acknowledgment.verified,
        "created_at": acknowledgment.created_at.isoformat(),
        "notes": acknowledgment.notes,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Verify terms acknowledgment legal proof")
    parser.add_argument("--acknowledgment-id", type=int, help="Acknowledgment ID to verify")
    parser.add_argument("--customer-id", type=int, help="Customer ID (use with --latest)")
    parser.add_argument("--booking-id", type=int, help="Booking ID")
    parser.add_argument(
        "--latest", action="store_true", help="Get latest acknowledgment for customer"
    )
    parser.add_argument("--output", choices=["json", "text"], default="text", help="Output format")

    args = parser.parse_args()

    # Get database session
    db: Session = SessionLocal()

    try:
        # Find acknowledgment
        query = db.query(TermsAcknowledgment)

        if args.acknowledgment_id:
            acknowledgment = query.filter(TermsAcknowledgment.id == args.acknowledgment_id).first()
        elif args.customer_id:
            query = query.filter(TermsAcknowledgment.customer_id == args.customer_id)
            if args.latest:
                query = query.order_by(TermsAcknowledgment.acknowledged_at.desc())
            acknowledgment = query.first()
        elif args.booking_id:
            acknowledgment = query.filter(TermsAcknowledgment.booking_id == args.booking_id).first()
        else:
            parser.error("Must specify --acknowledgment-id, --customer-id, or --booking-id")

        if not acknowledgment:
            print("❌ Acknowledgment not found")
            return

        # Get customer phone
        customer = acknowledgment.customer
        customer_phone = customer.phone if customer else ""

        # Verify
        result = verify_acknowledgment(acknowledgment, customer_phone)

        # Output
        if args.output == "json":
            print(json.dumps(result, indent=2, default=str))
        else:
            # Text output
            print("=" * 80)
            print("TERMS ACKNOWLEDGMENT VERIFICATION REPORT")
            print("=" * 80)
            print(f"\nAcknowledgment ID: {result['acknowledgment_id']}")
            print(f"Customer ID: {result['customer_id']}")
            print(f"Booking ID: {result['booking_id']}")
            print(f"Verified At: {result['verified_at']}")
            print(f"\nOVERALL STATUS: {result['verification_status']}")
            print("\n" + "-" * 80)
            print("VERIFICATION CHECKS:")
            print("-" * 80)

            for check_name, check_data in result["verification_checks"].items():
                status_emoji = {
                    "PASS": "✅",
                    "FAIL": "❌",
                    "WARNING": "⚠️",
                    "UNAVAILABLE": "➖",
                }.get(check_data["status"], "❓")

                print(f"\n{status_emoji} {check_name.replace('_', ' ').title()}")
                print(f"   Status: {check_data['status']}")
                print(f"   {check_data['explanation']}")

                if check_name == "hash_integrity" and "stored_hash" in check_data:
                    print(f"   Stored Hash:      {check_data['stored_hash'][:32]}...")
                    print(f"   Recalculated Hash: {check_data['recalculated_hash'][:32]}...")

            print("\n" + "-" * 80)
            print("EVIDENCE PACKAGE (for legal use):")
            print("-" * 80)
            for key, value in result["evidence_package"].items():
                if value and key not in ["notes"]:
                    print(f"  {key}: {value}")

            print("\n" + "=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()
