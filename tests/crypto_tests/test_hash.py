"""
test_hash.py  —  pytest test suite for hash.py
Run with:  pytest tests/crypto_tests/test_hash.py -v
"""

import pytest
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." , "..", "crypto"))
from hash import (
    tth,
    secure_hash,
    hash_n2,
    _encode_char,
    _encode,
    _pad,
    _mix,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  1. _encode_char()
# ═══════════════════════════════════════════════════════════════════════════════

class TestEncodeChar:

    def test_digit_0(self):
        assert _encode_char("0") == 0

    def test_digit_9(self):
        assert _encode_char("9") == 9

    def test_letter_A_is_1(self):
        assert _encode_char("A") == 1

    def test_letter_Z_is_26(self):
        assert _encode_char("Z") == 26

    def test_letter_B_is_2(self):
        assert _encode_char("B") == 2

    def test_lowercase_equals_uppercase(self):
        for c in "abcdefghijklmnopqrstuvwxyz":
            assert _encode_char(c) == _encode_char(c.upper())

    def test_invalid_space_raises(self):
        with pytest.raises(ValueError):
            _encode_char(" ")

    def test_invalid_special_raises(self):
        with pytest.raises(ValueError):
            _encode_char("!")

    def test_invalid_pipe_raises(self):
        with pytest.raises(ValueError):
            _encode_char("|")


# ═══════════════════════════════════════════════════════════════════════════════
#  2. _encode()
# ═══════════════════════════════════════════════════════════════════════════════

class TestEncode:

    def test_returns_list(self):
        assert isinstance(_encode("ABC"), list)

    def test_correct_length(self):
        assert len(_encode("ABC123")) == 6

    def test_correct_values(self):
        assert _encode("A1B2") == [1, 1, 2, 2]

    def test_case_insensitive(self):
        assert _encode("abc") == _encode("ABC")

    def test_all_digits(self):
        assert _encode("0123456789") == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


# ═══════════════════════════════════════════════════════════════════════════════
#  3. _pad()
# ═══════════════════════════════════════════════════════════════════════════════

class TestPad:

    def test_already_multiple_of_16_unchanged(self):
        v = list(range(16))
        assert _pad(v) == v

    def test_32_chars_unchanged(self):
        v = list(range(32))
        assert _pad(v) == v

    def test_output_multiple_of_16(self):
        for n in [1, 3, 7, 12, 15, 17, 20, 31, 33]:
            result = _pad(list(range(n)))
            assert len(result) % 16 == 0, f"Failed for n={n}"

    def test_single_element_padded_to_16(self):
        result = _pad([5])
        assert len(result) == 16
        assert result[0] == 5

    def test_12_chars_padded_to_16(self):
        # N2 codes are 12 chars — this is the most common case
        v = list(range(12))
        result = _pad(v)
        assert len(result) == 16

    def test_padding_uses_start_of_values(self):
        # padding should be a cyclic repetition of the start
        v = [1, 2, 3]
        result = _pad(v)
        assert len(result) == 16
        # first 3 elements are original
        assert result[:3] == [1, 2, 3]

    def test_empty_raises_or_returns_empty(self):
        # edge case: empty list has remainder 0, should return as-is
        assert _pad([]) == []

    def test_custom_block_size(self):
        v = [1, 2, 3]
        result = _pad(v, block_size=8)
        assert len(result) == 8


# ═══════════════════════════════════════════════════════════════════════════════
#  4. _mix()
# ═══════════════════════════════════════════════════════════════════════════════

class TestMix:

    def test_returns_list_of_4(self):
        block = list(range(16))
        result = _mix(block)
        assert isinstance(result, list)
        assert len(result) == 4

    def test_all_values_in_byte_range(self):
        block = [i % 256 for i in range(16)]
        for v in _mix(block):
            assert 0 <= v <= 255

    def test_zero_block(self):
        block = [0] * 16
        result = _mix(block)
        assert all(0 <= v <= 255 for v in result)

    def test_max_block(self):
        block = [255] * 16
        result = _mix(block)
        assert all(0 <= v <= 255 for v in result)

    def test_different_blocks_different_output(self):
        block1 = list(range(16))
        block2 = list(range(1, 17))
        assert _mix(block1) != _mix(block2)

    def test_deterministic(self):
        block = [i * 3 % 256 for i in range(16)]
        assert _mix(block) == _mix(block)


# ═══════════════════════════════════════════════════════════════════════════════
#  5. tth()
# ═══════════════════════════════════════════════════════════════════════════════

class TestTth:

    def test_output_is_string(self):
        assert isinstance(tth("AF15GH258ZQP"), str)

    def test_output_is_8_hex_chars(self):
        result = tth("AF15GH258ZQP")
        assert len(result) == 8
        assert re.fullmatch(r"[0-9a-f]{8}", result)

    def test_deterministic(self):
        assert tth("AF15GH258ZQP") == tth("AF15GH258ZQP")

    def test_case_insensitive(self):
        assert tth("AF15GH258ZQP") == tth("af15gh258zqp")
        assert tth("GDVESGSDBHSBDDY783374") == tth("gdvesgsdbhsbddy783374")

    def test_different_inputs_different_hash(self):
        assert tth("AF15GH258ZQP") != tth("AF15GH258ZQR")

    def test_one_char_difference_changes_hash(self):
        # last char changed
        assert tth("GDVESGSDBHSBDDY783374") != tth("GDVESGSDBHSBDDY783375")

    def test_minimum_16_chars(self):
        result = tth("ABCDEFGHIJKLMNOP")
        assert len(result) == 8

    def test_12_char_N2_code(self):
        # typical N2 code length from the project
        result = tth("BZ99KL123MNP")
        assert len(result) == 8

    def test_short_input_no_crash(self):
        # padding fix should handle this
        result = tth("ABC")
        assert len(result) == 8

    def test_single_char_no_crash(self):
        result = tth("A")
        assert len(result) == 8

    def test_long_input(self):
        result = tth("A" * 100)
        assert len(result) == 8

    def test_all_digits(self):
        result = tth("123456789012")
        assert len(result) == 8

    def test_mixed_alphanumeric(self):
        result = tth("AB12CD34EF56")
        assert len(result) == 8

    # ── error cases ──────────────────────────────────────────────────────────


    def test_spaces_raise(self):
        with pytest.raises(ValueError):
            tth("hello world")

    def test_special_chars_raise(self):
        with pytest.raises(ValueError):
            tth("AB!CD")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            tth(123)


# ═══════════════════════════════════════════════════════════════════════════════
#  6. secure_hash()
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecureHash:

    def test_output_is_string(self):
        assert isinstance(secure_hash("BZ99KL123MNP"), str)

    def test_output_is_64_hex_chars(self):
        result = secure_hash("BZ99KL123MNP")
        assert len(result) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", result)

    def test_deterministic(self):
        assert secure_hash("BZ99KL123MNP") == secure_hash("BZ99KL123MNP")

    def test_case_insensitive(self):
        # secure_hash uppercases before hashing
        assert secure_hash("BZ99KL123MNP") == secure_hash("bz99kl123mnp")

    def test_different_inputs_different_hash(self):
        assert secure_hash("BZ99KL123MNP") != secure_hash("BZ99KL123MNQ")

    def test_one_char_difference_changes_hash(self):
        assert secure_hash("AAAAAAAAAAAAA") != secure_hash("AAAAAAAAAAAAB")

    def test_longer_output_than_tth(self):
        # SHA-256 = 64 chars,  TTH = 8 chars
        assert len(secure_hash("test")) > len(tth("test"))

    def test_different_from_tth(self):
        # they should never produce the same format output
        s = secure_hash("AF15GH258ZQP")
        t = tth("AF15GH258ZQP")
        assert len(s) != len(t)

    # ── error cases ──────────────────────────────────────────────────────────

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            secure_hash("")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            secure_hash(123)


# ═══════════════════════════════════════════════════════════════════════════════
#  7. hash_n2()  — unified interface
# ═══════════════════════════════════════════════════════════════════════════════

class TestHashN2:

    N2 = "BZ99KL123MNP"

    def test_default_uses_secure_hash(self):
        assert hash_n2(self.N2) == secure_hash(self.N2)

    def test_pedagogic_uses_tth(self):
        assert hash_n2(self.N2, pedagogic=True) == tth(self.N2)

    def test_default_is_64_chars(self):
        assert len(hash_n2(self.N2)) == 64

    def test_pedagogic_is_8_chars(self):
        assert len(hash_n2(self.N2, pedagogic=True)) == 8

    def test_deterministic_default(self):
        assert hash_n2(self.N2) == hash_n2(self.N2)

    def test_deterministic_pedagogic(self):
        assert hash_n2(self.N2, pedagogic=True) == hash_n2(self.N2, pedagogic=True)

    def test_case_insensitive_default(self):
        assert hash_n2(self.N2) == hash_n2(self.N2.lower())

    def test_case_insensitive_pedagogic(self):
        assert hash_n2(self.N2, pedagogic=True) == hash_n2(self.N2.lower(), pedagogic=True)

    def test_different_n2_different_hash_default(self):
        assert hash_n2("BZ99KL123MNP") != hash_n2("BZ99KL123MNQ")

    def test_different_n2_different_hash_pedagogic(self):
        assert hash_n2("BZ99KL123MNP", pedagogic=True) != hash_n2("BZ99KL123MNQ", pedagogic=True)

    def test_production_and_pedagogic_differ(self):
        # same input, different mode → different output
        assert hash_n2(self.N2) != hash_n2(self.N2, pedagogic=True)

    # ── error cases ──────────────────────────────────────────────────────────

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            hash_n2("")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            hash_n2(123)

    def test_special_chars_raise(self):
        with pytest.raises(ValueError):
            hash_n2("BZ99 KL123!")


# ═══════════════════════════════════════════════════════════════════════════════
#  8. Integration : commissioner workflow simulation
#     The commissioner hashes all N2 codes and stores fingerprints.
#     Later, he verifies submitted N2 codes against stored fingerprints.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommissionerWorkflow:

    def test_store_and_verify_production(self):
        """Commissioner stores SHA-256 fingerprints, verifies submitted N2."""
        voter_n2_codes = ["BZ99KL123MNP", "AF15GH258ZQP", "XX00YY111ZZA"]

        # Commissioner stores fingerprints (N2 list is then destroyed)
        fingerprints = {hash_n2(n2) for n2 in voter_n2_codes}

        # Counter submits N2 from a ballot — commissioner verifies
        submitted_n2 = "AF15GH258ZQP"
        assert hash_n2(submitted_n2) in fingerprints

    def test_store_and_verify_pedagogic(self):
        """Same workflow using TTH (for subject exercises)."""
        voter_n2_codes = ["BZ99KL123MNP", "AF15GH258ZQP", "XX00YY111ZZA"]

        fingerprints = {hash_n2(n2, pedagogic=True) for n2 in voter_n2_codes}

        submitted_n2 = "AF15GH258ZQP"
        assert hash_n2(submitted_n2, pedagogic=True) in fingerprints

    def test_forged_n2_not_in_fingerprints(self):
        """A fake N2 code must not match any stored fingerprint."""
        voter_n2_codes = ["BZ99KL123MNP", "AF15GH258ZQP"]
        fingerprints = {hash_n2(n2) for n2 in voter_n2_codes}

        forged_n2 = "ZZZZZZZZZZZZ"
        assert hash_n2(forged_n2) not in fingerprints

    def test_fingerprints_are_unique(self):
        """All N2 codes must produce distinct fingerprints."""
        from encoding import generate_code
        n2_codes = [generate_code() for _ in range(100)]
        fingerprints = [hash_n2(n2) for n2 in n2_codes]
        assert len(set(fingerprints)) == 100