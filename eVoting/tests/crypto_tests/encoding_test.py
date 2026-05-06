"""
test_encoding.py  —  pytest test suite for encoding.py
Run with:  pytest test_encoding.py -v
"""

import pytest
import re
import sys
import os


import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." , "..", "crypto"))

from encoding import tth, generate_code, format_code, encode_message, encode_vote

# RSA-2048 generated once and shared across tests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

_PRIVATE_KEY  = rsa.generate_private_key(public_exponent=65537, key_size=2048,
                                          backend=default_backend())
RSA_2048_N    = _PRIVATE_KEY.private_numbers().public_numbers.n  
RSA_SMALL_N   = 583   


# ═══════════════════════════════════════════════════════════════════════════════
#  1. tth()
# ═══════════════════════════════════════════════════════════════════════════════

class TestTth:

    def test_output_is_8_hex_chars(self):
        result = tth("AF15GH258ZQP")
        assert len(result) == 8
        assert re.fullmatch(r"[0-9a-fA-F]{8}", result)

    def test_deterministic(self):
        assert tth("AF15GH258ZQP") == tth("AF15GH258ZQP")

    def test_case_insensitive(self):
        assert tth("AF15GH258ZQP") == tth("af15gh258zqp")

    def test_different_inputs_different_outputs(self):
        assert tth("AF15GH258ZQP") != tth("AF15GH258ZQR")

    def test_single_char(self):
        result = tth("A")
        assert len(result) == 8

    # ── error cases ──────────────────────────────────────────────────────────

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            tth("")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            tth(123)

    def test_spaces_raise(self):
        with pytest.raises(ValueError):
            tth("hello world")

    def test_special_chars_raise(self):
        with pytest.raises(ValueError):
            tth("hello!")

    def test_pipe_raises(self):
        with pytest.raises(ValueError):
            tth("AB|CD")


# ═══════════════════════════════════════════════════════════════════════════════
#  2. generate_code()
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateCode:

    def test_default_length_is_12(self):
        assert len(generate_code()) == 12

    def test_custom_length(self):
        for n in [1, 4, 8, 16, 32]:
            assert len(generate_code(n)) == n

    def test_only_uppercase_alphanumeric(self):
        for _ in range(200):
            code = generate_code()
            assert re.fullmatch(r"[A-Z0-9]+", code), f"Bad char in: {code}"

    def test_high_uniqueness(self):
        codes = [generate_code() for _ in range(1000)]
        assert len(set(codes)) > 990

    def test_uses_full_alphabet(self):
        """Over 5000 codes, every character of the alphabet must appear."""
        chars = set("".join(generate_code() for _ in range(5000)))
        full_alphabet = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        assert full_alphabet.issubset(chars)

    # ── error cases ──────────────────────────────────────────────────────────

    def test_zero_length_raises(self):
        with pytest.raises(ValueError):
            generate_code(0)

    def test_negative_length_raises(self):
        with pytest.raises(ValueError):
            generate_code(-5)

    def test_float_length_raises(self):
        with pytest.raises(TypeError):
            generate_code(12.0)

    def test_string_length_raises(self):
        with pytest.raises(TypeError):
            generate_code("12")


# ═══════════════════════════════════════════════════════════════════════════════
#  3. format_code()
# ═══════════════════════════════════════════════════════════════════════════════

class TestFormatCode:

    def test_default_group_size_4(self):
        assert format_code("AF15GH258ZQP") == "AF15 GH25 8ZQP"

    def test_custom_group_size_2(self):
        assert format_code("ABCDEFGH", group_size=2) == "AB CD EF GH"

    def test_custom_group_size_3(self):
        assert format_code("ABCDEFGHI", group_size=3) == "ABC DEF GHI"

    def test_uppercases_input(self):
        assert format_code("abcd") == "ABCD"

    def test_exact_group_fit(self):
        assert format_code("ABCD", group_size=4) == "ABCD"

    def test_single_char(self):
        assert format_code("A") == "A"

    def test_group_larger_than_code(self):
        assert format_code("AB", group_size=10) == "AB"

    # ── error cases ──────────────────────────────────────────────────────────

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            format_code("")

    def test_spaces_raise(self):
        with pytest.raises(ValueError):
            format_code("hello world")

    def test_special_chars_raise(self):
        with pytest.raises(ValueError):
            format_code("AB-CD")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            format_code(1234)

    def test_zero_group_size_raises(self):
        with pytest.raises(ValueError):
            format_code("ABCD", group_size=0)

    def test_float_group_size_raises(self):
        with pytest.raises(TypeError):
            format_code("ABCD", group_size=2.0)


# ═══════════════════════════════════════════════════════════════════════════════
#  4. encode_message()
# ═══════════════════════════════════════════════════════════════════════════════

class TestEncodeMessage:

    # ── no modulus : raw SHA-256 integer ─────────────────────────────────────

    def test_returns_positive_integer(self):
        assert encode_message("hello") > 0

    def test_deterministic(self):
        assert encode_message("hello") == encode_message("hello")

    def test_different_messages_different_results(self):
        assert encode_message("hello") != encode_message("world")

    def test_no_modulus_returns_full_sha256_int(self):
        import hashlib
        expected = int.from_bytes(hashlib.sha256(b"hello").digest(), "big")
        assert encode_message("hello") == expected

    # ── with small modulus  ───────────────────────────────

    def test_result_in_range_small_N(self):
        N = RSA_SMALL_N
        m = encode_message("hello", rsa_modulus=N)
        assert 1 <= m <= N - 1

    def test_never_zero_small_N(self):
        N = RSA_SMALL_N
        for msg in ["hello", "world", "vote", "N2code", "test123"]:
            assert encode_message(msg, rsa_modulus=N) != 0

    # ── 2048-bit modulus (PSS padding) ──────────────────────────────

    def test_result_in_range_2048(self):
        m = encode_message("hello", rsa_modulus=RSA_2048_N)
        assert 1 <= m <= RSA_2048_N - 1

    def test_never_zero_2048(self):
        for msg in ["hello", "world", "vote", "N2code", "test123"]:
            assert encode_message(msg, rsa_modulus=RSA_2048_N) != 0

    def test_deterministic_with_2048(self):
        m1 = encode_message("hello", rsa_modulus=RSA_2048_N)
        m2 = encode_message("hello", rsa_modulus=RSA_2048_N)
        assert m1 == m2

    def test_different_msgs_different_2048(self):
        m1 = encode_message("hello", rsa_modulus=RSA_2048_N)
        m2 = encode_message("world", rsa_modulus=RSA_2048_N)
        assert m1 != m2

    def test_padding_fills_modulus_size(self):
        """Result should be large — PSS fills the full modulus space."""
        m = encode_message("hello", rsa_modulus=RSA_2048_N)
        # should use most of the 2048 bits, not a tiny number
        assert m.bit_length() > 100

    # ── error cases ──────────────────────────────────────────────────────────

    def test_empty_msg_raises(self):
        with pytest.raises(ValueError):
            encode_message("")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            encode_message(42)

    def test_modulus_less_than_2_raises(self):
        with pytest.raises(ValueError):
            encode_message("hello", rsa_modulus=1)

    def test_modulus_zero_raises(self):
        with pytest.raises(ValueError):
            encode_message("hello", rsa_modulus=0)

    def test_modulus_float_raises(self):
        with pytest.raises(TypeError):
            encode_message("hello", rsa_modulus=55.0)


# ═══════════════════════════════════════════════════════════════════════════════
#  5. encode_vote()
# ═══════════════════════════════════════════════════════════════════════════════

class TestEncodeVote:

    N2 = "BZ99KL123MNP"

    # ── correctness ──────────────────────────────────────────────────────────

    def test_deterministic(self):
        v1 = encode_vote(8, self.N2)
        v2 = encode_vote(8, self.N2)
        assert v1 == v2

    def test_different_votes_different_encoding(self):
        assert encode_vote(7, self.N2) != encode_vote(8, self.N2)

    def test_different_N2_different_encoding(self):
        assert encode_vote(8, self.N2) != encode_vote(8, "XX00YY111ZZA")

    def test_case_insensitive_N2(self):
        assert encode_vote(8, self.N2.lower()) == encode_vote(8, self.N2.upper())

    def test_vote_zero_allowed(self):
        result = encode_vote(0, self.N2)
        assert result > 0

    # ── with modulus ─────────────────────────────────────────────────────────

    def test_result_in_range_small_N(self):
        v = encode_vote(8, self.N2, rsa_modulus=RSA_SMALL_N)
        assert 1 <= v <= RSA_SMALL_N - 1

    def test_result_in_range_2048(self):
        v = encode_vote(8, self.N2, rsa_modulus=RSA_2048_N)
        assert 1 <= v <= RSA_2048_N - 1

    def test_never_zero_with_modulus(self):
        for vote in range(10):
            assert encode_vote(vote, self.N2, rsa_modulus=RSA_SMALL_N) != 0

    # ── binding : vote and N2 are both captured ───────────────────────────────

    def test_vote_and_N2_both_affect_result(self):
        """Change only vote → different; change only N2 → different."""
        base  = encode_vote(5, "AAABBB111222")
        diff1 = encode_vote(6, "AAABBB111222")   # different vote
        diff2 = encode_vote(5, "AAABBB111223")   # different N2
        assert base != diff1
        assert base != diff2
        assert diff1 != diff2

    # ── error cases ──────────────────────────────────────────────────────────

    def test_negative_vote_raises(self):
        with pytest.raises(ValueError):
            encode_vote(-1, self.N2)

    def test_float_vote_raises(self):
        with pytest.raises(TypeError):
            encode_vote(1.0, self.N2)

    def test_empty_N2_raises(self):
        with pytest.raises(ValueError):
            encode_vote(8, "")

    def test_special_chars_in_N2_raise(self):
        with pytest.raises(ValueError):
            encode_vote(8, "bad code!!!")

    def test_spaces_in_N2_raise(self):
        with pytest.raises(ValueError):
            encode_vote(8, "AB CD EF GH")

    def test_non_string_N2_raises(self):
        with pytest.raises(TypeError):
            encode_vote(8, 12345)


# ═══════════════════════════════════════════════════════════════════════════════
#  6. Électeur → Administrateur → Électeur → Décompteur
# ═══════════════════════════════════════════════════════════════════════════════

class TestBlindSignatureFlow:
    """
    Simulates the complete Chaum blind signature protocol using RSA-2048.
    """

    def test_full_flow(self):
        import math

        # ── Keys (Administrateur) ────────────────────────────────────────────
        priv   = _PRIVATE_KEY
        pub    = priv.public_key()
        nums   = priv.private_numbers()
        d      = nums.d
        e      = nums.public_numbers.e
        N      = nums.public_numbers.n

        # ── Électeur : encode ballot ─────────────────────────────────────────
        vote   = 7
        N2     = "BZ99KL123MNP"
        m      = encode_vote(vote, N2, rsa_modulus=N)
        assert 1 <= m <= N - 1

        # ── Électeur : choose blinding factor k, coprime with N ──────────────
        import secrets as _sec
        while True:
            k = _sec.randbelow(N - 2) + 2
            if math.gcd(k, N) == 1:
                break

        # ── Électeur : blind  m' = m * k^e mod N ────────────────────────────
        m_prime = (m * pow(k, e, N)) % N

        # ── Administrateur : sign  m'' = (m')^d mod N ───────────────────────
        m_double_prime = pow(m_prime, d, N)

        # ── Électeur : unblind  s = m'' * k^-1 mod N ────────────────────────
        k_inv = pow(k, -1, N)
        s     = (m_double_prime * k_inv) % N

        # ── Décompteur : verify  s^e mod N == m ─────────────────────────────
        assert pow(s, e, N) == m, "Blind signature verification FAILED"

    def test_different_voters_independent(self):
        """Two voters with different N2 produce different m values."""
        import math, secrets as _sec

        nums = _PRIVATE_KEY.private_numbers()
        N    = nums.public_numbers.n

        m1 = encode_vote(5, "AAABBB111222", rsa_modulus=N)
        m2 = encode_vote(5, "CCCDDD333444", rsa_modulus=N)
        assert m1 != m2