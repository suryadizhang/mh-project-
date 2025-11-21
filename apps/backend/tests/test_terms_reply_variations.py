"""
Test Cases for Terms Reply Typo & Variation Handling

Run with: pytest tests/test_terms_reply_variations.py -v
"""

import pytest
from services.terms_acknowledgment_service import TermsAcknowledgmentService
from schemas.terms_acknowledgment import SMSTermsVerification


class TestTermsReplyVariations:
    """Test that we correctly handle typos and variations in customer SMS replies"""

    @pytest.fixture
    def service(self, db_session):
        return TermsAcknowledgmentService(db_session)

    # ========================================
    # STANDARD PHRASES (Should Always Work)
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "I AGREE",
            "AGREE",
            "YES",
            "CONFIRM",
            "ACCEPT",
            "OK",
            "OKAY",
        ],
    )
    def test_standard_phrases(self, service, reply_text):
        """Standard phrases should always be accepted"""
        verification = SMSTermsVerification(
            customer_phone="2103884155", reply_text=reply_text, booking_id=123
        )

        # Should validate (internal check)
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # CASE VARIATIONS
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "i agree",  # lowercase
            "I Agree",  # title case
            "I aGrEe",  # mixed case
            "AGREE",  # uppercase
            "agree",  # lowercase
            "Yes",  # title case
            "yes",  # lowercase
            "ok",  # lowercase
            "Ok",  # title case
        ],
    )
    def test_case_variations(self, service, reply_text):
        """Case variations should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # TYPOS - "I AGREE"
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "I agre",  # missing E
            "I agee",  # missing R
            "IAGREE",  # no space
            "I aggree",  # double G
            "I arree",  # double R
            "I agrre",  # RR instead of RE
            "I AGRE",  # uppercase, missing E
        ],
    )
    def test_i_agree_typos(self, service, reply_text):
        """Common typos of 'I AGREE' should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # TYPOS - "AGREE"
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "agre",  # missing E
            "agee",  # missing R
            "aggree",  # double G
            "aree",  # missing G
            "agrre",  # extra R
            "agreee",  # triple E
            "AGRE",  # uppercase
        ],
    )
    def test_agree_typos(self, service, reply_text):
        """Common typos of 'AGREE' should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # TYPOS - "YES"
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "yep",  # variation
            "yeah",  # variation
            "yup",  # variation
            "ya",  # abbreviation
            "y",  # single letter
            "yea",  # missing S
            "ys",  # missing E
            "yse",  # swapped letters
            "yess",  # double S
            "yesss",  # triple S
        ],
    )
    def test_yes_variations(self, service, reply_text):
        """Variations and typos of 'YES' should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # TYPOS - "OKAY"
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "ok",
            "okey",
            "okie",
            "okya",  # YA instead of AY
            "oaky",  # swapped K/A
            "oky",  # missing A
            "okayy",  # double Y
            "okaay",  # double A
            "okat",  # T instead of Y
            "okau",  # U instead of Y (keyboard)
            "okqy",  # Q instead of A (keyboard adjacent)
            "okwy",  # W instead of A (keyboard adjacent)
        ],
    )
    def test_okay_typos(self, service, reply_text):
        """Common typos of 'OKAY' should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # TYPOS - "CONFIRM"
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "comfirm",  # M instead of N
            "confrim",  # swapped I/R
            "confirn",  # N instead of M
            "comfrim",  # both swaps
            "confir",  # missing M
        ],
    )
    def test_confirm_typos(self, service, reply_text):
        """Common typos of 'CONFIRM' should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # SMS ABBREVIATIONS
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "k",
            "kk",
            "kay",
            "okie dokie",
        ],
    )
    def test_sms_abbreviations(self, service, reply_text):
        """SMS abbreviations should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # ENTHUSIASTIC RESPONSES
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "yes!",
            "agree!",
            "ok!",
            "I agree!",
            "yess!",
            "yesss!",
            "okay!",
            "YES!!",
            "AGREE!!!",
        ],
    )
    def test_enthusiastic_responses(self, service, reply_text):
        """Enthusiastic responses with punctuation should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # CASUAL VARIATIONS
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "yup",
            "sure",
            "fine",
            "affirmative",
            "absolutely",
            "definitely",
            "certainly",
        ],
    )
    def test_casual_variations(self, service, reply_text):
        """Casual but clear affirmative responses should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # PUNCTUATION VARIATIONS
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "I agree.",
            "I agree!",
            "I agree!!",
            "okay.",
            "yes.",
            "agree,",
            "yes...",
            "okay???",
        ],
    )
    def test_punctuation_variations(self, service, reply_text):
        """Responses with punctuation should be accepted"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # WHITESPACE VARIATIONS
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "I  agree",  # double space
            " I agree ",  # leading/trailing
            "Iagree",  # no space
            "  yes  ",  # multiple spaces
        ],
    )
    def test_whitespace_variations(self, service, reply_text):
        """Whitespace variations should be handled"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # MULTIPLE WORDS (Should Still Work)
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "yes I agree",
            "ok I accept",
            "sure, I agree",
            "I totally agree",
            "yes please",
            "okay thanks",
        ],
    )
    def test_multiple_words(self, service, reply_text):
        """Responses with multiple words containing valid phrase should work"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # FUZZY MATCHING EDGE CASES
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "agre",  # AGREE missing E (4 letters, has A,G,R,E)
            "aerg",  # AGREE scrambled
            "yse",  # YES scrambled (3 letters)
            "ko",  # OK reversed (2 letters)
        ],
    )
    def test_fuzzy_matching(self, service, reply_text):
        """Fuzzy matching should catch extreme typos"""
        assert service._is_valid_confirmation(reply_text)

    # ========================================
    # INVALID REPLIES (Should Be Rejected)
    # ========================================

    @pytest.mark.parametrize(
        "reply_text",
        [
            "maybe",
            "I guess",
            "probably",
            "nah",
            "no",
            "idk",
            "whatever",
            "sounds good",
            "lol ok",
            "sure why not",
            "👍",  # emoji only
            "...",  # dots only
            "???",  # questions only
            "huh",
            "what",
        ],
    )
    def test_invalid_replies(self, service, reply_text):
        """Ambiguous or negative replies should be rejected"""
        assert not service._is_valid_confirmation(reply_text)

    # ========================================
    # REAL-WORLD EXAMPLES
    # ========================================

    def test_real_world_scenario_1(self, service):
        """Customer fat-fingers 'I agree' as 'I agre'"""
        assert service._is_valid_confirmation("I agre")

    def test_real_world_scenario_2(self, service):
        """Customer types 'ok' in lowercase on mobile"""
        assert service._is_valid_confirmation("ok")

    def test_real_world_scenario_3(self, service):
        """Customer types 'yup' casually"""
        assert service._is_valid_confirmation("yup")

    def test_real_world_scenario_4(self, service):
        """Customer enthusiastically types 'yes!!!'"""
        assert service._is_valid_confirmation("yes!!!")

    def test_real_world_scenario_5(self, service):
        """Customer forgets space: 'Iagree'"""
        assert service._is_valid_confirmation("Iagree")

    def test_real_world_scenario_6(self, service):
        """Customer types SMS abbreviation 'k'"""
        assert service._is_valid_confirmation("k")

    def test_real_world_scenario_7(self, service):
        """Customer adds extra letters: 'okayy'"""
        assert service._is_valid_confirmation("okayy")

    def test_real_world_scenario_8(self, service):
        """Customer types with periods: 'I agree.'"""
        assert service._is_valid_confirmation("I agree.")

    # ========================================
    # BOUNDARY CASES
    # ========================================

    def test_empty_string(self, service):
        """Empty string should be rejected"""
        assert not service._is_valid_confirmation("")

    def test_only_whitespace(self, service):
        """Only whitespace should be rejected"""
        assert not service._is_valid_confirmation("   ")

    def test_very_long_text_with_valid_phrase(self, service):
        """Long text containing valid phrase should work"""
        assert service._is_valid_confirmation(
            "I have read the terms and conditions and I agree to them"
        )

    def test_very_long_text_without_valid_phrase(self, service):
        """Long text without valid phrase should be rejected"""
        assert not service._is_valid_confirmation(
            "I have read the document and might consider it later"
        )


class TestTermsReplyIntegration:
    """Integration tests with full acknowledgment flow"""

    @pytest.fixture
    def service(self, db_session):
        return TermsAcknowledgmentService(db_session)

    @pytest.fixture
    def customer(self, db_session):
        from models.customer import Customer

        customer = Customer(name="Test Customer", phone="2103884155", email="test@example.com")
        db_session.add(customer)
        db_session.commit()
        return customer

    async def test_full_flow_with_typo(self, service, customer):
        """Test complete acknowledgment flow with typo in reply"""
        verification = SMSTermsVerification(
            customer_phone="2103884155", reply_text="i agre", booking_id=123  # Typo + lowercase
        )

        acknowledgment = await service.verify_sms_acknowledgment(
            verification=verification,
            customer_id=customer.id,
            message_id="TEST-12345",
            message_timestamp="2025-01-03T14:30:00Z",
            message_hash="abc123def456",
            webhook_source_ip="127.0.0.1",
        )

        # Should be accepted despite typo
        assert acknowledgment is not None
        assert acknowledgment.customer_id == customer.id
        assert acknowledgment.acknowledgment_text == "i agre"  # Original preserved
        assert acknowledgment.verified is True
        assert "RingCentral Message ID: TEST-12345" in acknowledgment.notes

    async def test_full_flow_with_invalid_reply(self, service, customer):
        """Test that invalid reply is rejected"""
        verification = SMSTermsVerification(
            customer_phone="2103884155", reply_text="maybe later", booking_id=123
        )

        acknowledgment = await service.verify_sms_acknowledgment(
            verification=verification, customer_id=customer.id
        )

        # Should be rejected
        assert acknowledgment is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
