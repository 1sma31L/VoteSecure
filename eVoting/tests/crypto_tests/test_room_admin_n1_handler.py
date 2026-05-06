"""
test_room_admin_n1_handler.py — pytest test suite for room_admin_N1_handler.py

Run with:  pytest test_room_admin_n1_handler.py -v
"""

import pytest
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "entities"))

from room_admin_N1_handler import (
    generate_code,
    format_code,
    generate_n1_codes,
    generate_room_code,
    CHARSET
)


# ═══════════════════════════════════════════════════════════════════════════════
#  1. CHARSET
# ═══════════════════════════════════════════════════════════════════════════════

class TestCharset:

    def test_charset_contains_digits(self):
        """CHARSET should include all digits 0-9."""
        assert "0" in CHARSET
        assert "1" in CHARSET
        assert "9" in CHARSET

    def test_charset_contains_uppercase_letters(self):
        """CHARSET should include all uppercase letters A-Z."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert letter in CHARSET, f"Missing {letter}"

    def test_charset_no_lowercase(self):
        """CHARSET should NOT contain lowercase letters."""
        for letter in "abcdefghijklmnopqrstuvwxyz":
            assert letter not in CHARSET

    def test_charset_no_special_chars(self):
        """CHARSET should NOT contain special characters."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"
        for char in special_chars:
            assert char not in CHARSET


# ═══════════════════════════════════════════════════════════════════════════════
#  2. generate_code()
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateCode:

    def test_default_length_12(self):
        """Default code length should be 12."""
        code = generate_code()
        assert len(code) == 12

    def test_custom_length(self):
        """generate_code() should respect custom length parameter."""
        for length in [1, 4, 8, 16, 32, 64]:
            code = generate_code(length=length)
            assert len(code) == length

    def test_output_is_string(self):
        """generate_code() should return a string."""
        code = generate_code()
        assert isinstance(code, str)

    def test_only_valid_characters(self):
        """Generated code should only contain characters from CHARSET."""
        for _ in range(100):
            code = generate_code()
            for char in code:
                assert char in CHARSET, f"Invalid char: {char}"

    def test_only_uppercase_alphanumeric(self):
        """Generated code should match regex [A-Z0-9]+."""
        for _ in range(100):
            code = generate_code()
            assert re.fullmatch(r"[A-Z0-9]+", code), f"Invalid code: {code}"

    def test_randomness_high_uniqueness(self):
        """Multiple calls should generate different codes (high probability)."""
        codes = [generate_code() for _ in range(1000)]
        unique_codes = len(set(codes))
        # Should have at least 99% unique (allow for random collisions)
        assert unique_codes > 990

    def test_uses_full_character_set(self):
        """Over many generations, all charset characters should appear."""
        chars = set("".join(generate_code() for _ in range(5000)))
        assert chars == set(CHARSET)

    def test_zero_length(self):
        """generate_code(0) should return empty string."""
        code = generate_code(length=0)
        assert code == ""
        assert len(code) == 0

    def test_large_length(self):
        """Should handle large length values."""
        code = generate_code(length=1000)
        assert len(code) == 1000
        assert all(c in CHARSET for c in code)

    # ── error cases ──────────────────────────────────────────────────────────

    def test_float_length_raises(self):
        """Float length should raise TypeError."""
        with pytest.raises(TypeError):
            generate_code(length=12.5)

    def test_string_length_raises(self):
        """String length should raise TypeError."""
        with pytest.raises(TypeError):
            generate_code(length="12")

    def test_none_length_raises(self):
        """None as length should raise TypeError."""
        with pytest.raises(TypeError):
            generate_code(length=None)


# ═══════════════════════════════════════════════════════════════════════════════
#  3. format_code()
# ═══════════════════════════════════════════════════════════════════════════════

class TestFormatCode:

    def test_default_formatting_groups_of_4(self):
        """Default format_code() should group by 4 characters."""
        code = "ABCDEFGHIJKL"
        assert format_code(code) == "ABCD EFGH IJKL"

    def test_exact_groups_of_4(self):
        """Code exactly divisible by 4 should have clean spacing."""
        assert format_code("ABCD") == "ABCD"
        assert format_code("ABCDEFGH") == "ABCD EFGH"

    def test_partial_last_group(self):
        """Last group with less than 4 chars should be kept as-is."""
        assert format_code("ABCDEFGHIJ") == "ABCD EFGH IJ"
        assert format_code("ABCDEFGHIJK") == "ABCD EFGH IJK"
        assert format_code("ABCDEFGHIJKL") == "ABCD EFGH IJKL"

    def test_single_character(self):
        """Single character should be returned as-is."""
        assert format_code("A") == "A"

    def test_two_characters(self):
        """Two characters should be returned as-is."""
        assert format_code("AB") == "AB"

    def test_three_characters(self):
        """Three characters should be returned as-is."""
        assert format_code("ABC") == "ABC"

    def test_five_characters(self):
        """Five characters should produce one group and one remainder."""
        assert format_code("ABCDE") == "ABCD E"

    def test_preserves_input_uppercase(self):
        """Already uppercase input should be preserved."""
        code = "ABCD1234"
        assert format_code(code) == "ABCD 1234"

    def test_output_type_is_string(self):
        """format_code() should return a string."""
        result = format_code("ABCDEF")
        assert isinstance(result, str)

    def test_only_spaces_between_groups(self):
        """Output should only contain the input characters and spaces."""
        code = "ABCDEFGHIJ"
        result = format_code(code)
        assert result.count(" ") == 2  # Two spaces for 3 groups
        assert all(c in code or c == " " for c in result)

    # ── error cases ──────────────────────────────────────────────────────────

    def test_non_string_input_raises(self):
        """Non-string input should raise TypeError."""
        with pytest.raises(TypeError):
            format_code(12345)

    def test_none_input_raises(self):
        """None input should raise TypeError."""
        with pytest.raises(TypeError):
            format_code(None)

    def test_list_input_raises(self):
        """List input should raise TypeError."""
        with pytest.raises(TypeError):
            format_code(["A", "B", "C"])


# ═══════════════════════════════════════════════════════════════════════════════
#  4. generate_n1_codes()
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateN1Codes:

    def test_returns_dict(self):
        """generate_n1_codes() should return a dictionary."""
        result = generate_n1_codes(5)
        assert isinstance(result, dict)

    def test_correct_number_of_codes(self):
        """Should generate exactly num_voters codes."""
        for num in [1, 5, 10, 100]:
            result = generate_n1_codes(num)
            assert len(result) == num

    def test_keys_are_voter_ids(self):
        """Dictionary keys should be voter IDs from 1 to num_voters."""
        result = generate_n1_codes(5)
        assert set(result.keys()) == {1, 2, 3, 4, 5}

    def test_values_are_strings(self):
        """Dictionary values should be strings (codes)."""
        result = generate_n1_codes(5)
        for code in result.values():
            assert isinstance(code, str)

    def test_codes_have_default_length(self):
        """Each code should have default length of 12."""
        result = generate_n1_codes(5)
        for code in result.values():
            assert len(code) == 12

    def test_all_codes_unique(self):
        """All generated codes should be unique."""
        result = generate_n1_codes(100)
        codes = list(result.values())
        assert len(set(codes)) == 100

    def test_codes_contain_valid_chars(self):
        """All codes should contain only valid characters."""
        result = generate_n1_codes(10)
        for code in result.values():
            assert re.fullmatch(r"[A-Z0-9]{12}", code)

    def test_sequential_voter_ids(self):
        """Voter IDs should be sequential starting from 1."""
        result = generate_n1_codes(7)
        assert sorted(result.keys()) == list(range(1, 8))

    def test_single_voter(self):
        """Should handle single voter correctly."""
        result = generate_n1_codes(1)
        assert len(result) == 1
        assert 1 in result
        assert len(result[1]) == 12

    def test_large_number_of_voters(self):
        """Should handle large number of voters."""
        result = generate_n1_codes(1000)
        assert len(result) == 1000
        assert len(set(result.values())) == 1000  # All unique

    # ── error cases ──────────────────────────────────────────────────────────

    def test_float_voters_raises(self):
        """Float number of voters should raise TypeError."""
        with pytest.raises(TypeError):
            generate_n1_codes(5.5)

    def test_string_voters_raises(self):
        """String number of voters should raise TypeError."""
        with pytest.raises(TypeError):
            generate_n1_codes("5")

    def test_none_voters_raises(self):
        """None number of voters should raise TypeError."""
        with pytest.raises(TypeError):
            generate_n1_codes(None)


# ═══════════════════════════════════════════════════════════════════════════════
#  5. generate_room_code()
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateRoomCode:

    def test_returns_string(self):
        """generate_room_code() should return a string."""
        result = generate_room_code()
        assert isinstance(result, str)

    def test_default_length_12(self):
        """Room code should have default length of 12."""
        code = generate_room_code()
        assert len(code) == 12

    def test_contains_valid_characters(self):
        """Room code should only contain valid charset characters."""
        code = generate_room_code()
        assert re.fullmatch(r"[A-Z0-9]{12}", code)

    def test_randomness_different_calls(self):
        """Multiple calls should generate different codes (high probability)."""
        codes = [generate_room_code() for _ in range(100)]
        unique_codes = len(set(codes))
        # Should have at least 98% unique
        assert unique_codes > 98

    def test_unformatted_is_12_chars(self):
        """Room code should be unformatted 12-character string."""
        code = generate_room_code()
        assert len(code) == 12
        assert " " not in code

    # ── error cases ──────────────────────────────────────────────────────────

    def test_no_parameters(self):
        """generate_room_code() takes no parameters."""
        # Calling with parameters should raise TypeError
        with pytest.raises(TypeError):
            generate_room_code(length=12)


# ═══════════════════════════════════════════════════════════════════════════════
#  Integration: Complete N1 Handler Workflows
# ═══════════════════════════════════════════════════════════════════════════════

class TestN1HandlerIntegration:
    """
    Test complete N1 handler workflows for voter registration and room setup.
    """

    def test_full_election_setup(self):
        """Complete setup: room code + N1 codes for voters."""
        # Generate room code
        room_code = generate_room_code()
        assert len(room_code) == 12
        
        # Generate N1 codes for 10 voters
        n1_codes = generate_n1_codes(10)
        assert len(n1_codes) == 10
        
        # Format and display (simulate election setup)
        formatted_room = format_code(room_code)
        assert " " in formatted_room  # Should have spaces

    def test_voter_registration_workflow(self):
        """Simulate voter registration with formatted codes."""
        # Generate codes
        n1_codes = generate_n1_codes(5)
        
        # Format each for display
        formatted_codes = {}
        for voter_id, code in n1_codes.items():
            formatted_codes[voter_id] = format_code(code)
        
        # Check formatting
        for formatted in formatted_codes.values():
            # Should have spaces and be formatted
            assert " " in formatted
            # Remove spaces to get original
            unformatted = formatted.replace(" ", "")
            assert len(unformatted) == 12

    def test_large_election_setup(self):
        """Setup for large election with many voters."""
        num_voters = 500
        
        # Generate all N1 codes
        n1_codes = generate_n1_codes(num_voters)
        assert len(n1_codes) == num_voters
        
        # All should be unique
        codes_list = list(n1_codes.values())
        assert len(set(codes_list)) == num_voters
        
        # All should be properly formatted
        for code in codes_list:
            formatted = format_code(code)
            unformatted = formatted.replace(" ", "")
            assert len(unformatted) == 12

    def test_room_code_distribution(self):
        """Room code is unique for each polling place."""
        # Generate multiple room codes (different polling places)
        room_codes = [generate_room_code() for _ in range(10)]
        
        # Should all be unique
        assert len(set(room_codes)) == 10

    def test_code_formatting_consistency(self):
        """Formatting the same code multiple times should be consistent."""
        original_code = "ABCD1234EFGH"
        
        formatted1 = format_code(original_code)
        formatted2 = format_code(original_code)
        formatted3 = format_code(original_code)
        
        assert formatted1 == formatted2 == formatted3

    def test_format_unformat_roundtrip(self):
        """Formatting then removing spaces should recover original."""
        code = generate_code(12)
        
        formatted = format_code(code)
        unformatted = formatted.replace(" ", "")
        
        assert unformatted == code

    def test_n1_codes_distribution(self):
        """N1 codes for different voters should be completely different."""
        n1_codes = generate_n1_codes(3)
        
        code1 = n1_codes[1]
        code2 = n1_codes[2]
        code3 = n1_codes[3]
        
        # All different
        assert code1 != code2
        assert code2 != code3
        assert code1 != code3
        
        # No overlap in characters at same position
        # (very high probability for 12-char random codes)
        positions_same = sum(1 for i in range(12) if code1[i] == code2[i])
        assert positions_same < 12  # At least some difference

    def test_display_workflow(self):
        """Complete voter display workflow."""
        # Generate codes
        n1_codes = generate_n1_codes(3)
        
        # Format for display
        display_lines = []
        for voter_id in sorted(n1_codes.keys()):
            code = n1_codes[voter_id]
            formatted = format_code(code)
            display_lines.append(f"Voter {voter_id}: {formatted}")
        
        assert len(display_lines) == 3
        # Each line should have formatted code with spaces
        for line in display_lines:
            assert " " in line

    def test_code_validity_check(self):
        """Verify generated codes have correct properties."""
        n1_codes = generate_n1_codes(10)
        
        for voter_id, code in n1_codes.items():
            # Must be 12 characters
            assert len(code) == 12
            
            # Must only contain valid characters
            assert all(c in CHARSET for c in code)
            
            # Can be formatted without error
            formatted = format_code(code)
            assert isinstance(formatted, str)
