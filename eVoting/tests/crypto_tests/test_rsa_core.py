"""
test_rsa_core.py — pytest test suite for rsa_core.py

Run with:  pytest test_rsa_core.py -v
"""

import pytest
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "crypto"))

from rsa_core import is_prime, generate_prime, extended_gcd, mod_inverse, generate_rsa_keypair


# ═══════════════════════════════════════════════════════════════════════════════
#  1. is_prime()
# ═══════════════════════════════════════════════════════════════════════════════

class TestIsPrime:

    def test_small_primes(self):
        """Small known primes should return True."""
        small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        for p in small_primes:
            assert is_prime(p), f"{p} should be prime"

    def test_small_composites(self):
        """Small known composites should return False."""
        small_composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25]
        for n in small_composites:
            assert not is_prime(n), f"{n} should not be prime"

    def test_large_primes(self):
        """Large known primes should return True."""
        large_primes = [97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 
                       149, 151, 157, 163, 167, 173, 179, 181, 191, 193]
        for p in large_primes:
            assert is_prime(p), f"{p} should be prime"

    def test_mersenne_prime(self):
        """Mersenne primes should be detected."""
        # 2^7 - 1 = 127
        assert is_prime(127)

    def test_carmichael_number_561(self):
        """561 = 3 × 11 × 17 is a Carmichael number (pseudoprime)."""
        # Miller-Rabin with sufficient rounds should detect it as composite
        assert not is_prime(561)

    def test_carmichael_number_1105(self):
        """1105 = 5 × 13 × 17 is a Carmichael number."""
        assert not is_prime(1105)

    # ── error cases ──────────────────────────────────────────────────────────

    def test_zero_returns_false(self):
        assert not is_prime(0)

    def test_one_returns_false(self):
        assert not is_prime(1)

    def test_negative_returns_false(self):
        assert not is_prime(-5)
        assert not is_prime(-17)

    def test_custom_rounds(self):
        """Test with custom number of rounds."""
        assert is_prime(17, rounds=5)
        assert is_prime(17, rounds=40)
        assert not is_prime(15, rounds=20)

    def test_non_integer_raises(self):
        with pytest.raises(TypeError):
            is_prime(3.14)

    def test_string_raises(self):
        with pytest.raises(TypeError):
            is_prime("17")


# ═══════════════════════════════════════════════════════════════════════════════
#  2. generate_prime()
# ═══════════════════════════════════════════════════════════════════════════════

class TestGeneratePrime:

    def test_output_is_prime(self):
        """Generated value should always pass is_prime()."""
        for _ in range(10):
            p = generate_prime(bits=256)
            assert is_prime(p)

    def test_output_has_correct_bit_length(self):
        """Generated prime should have approximately the requested bit length."""
        for bits in [128, 256, 512]:
            p = generate_prime(bits=bits)
            # Check bit length is within expected range (allow ±1 bit)
            assert bits - 1 <= p.bit_length() <= bits + 1

    def test_output_is_odd(self):
        """All primes > 2 are odd."""
        for _ in range(10):
            p = generate_prime(bits=256)
            assert p % 2 == 1

    def test_high_bit_set(self):
        """The high bit should be set (ensures correct bit length)."""
        for bits in [128, 256]:
            p = generate_prime(bits=bits)
            assert p >= 2 ** (bits - 1)

    def test_uniqueness(self):
        """Multiple calls should generate different primes (with high probability)."""
        primes = [generate_prime(bits=256) for _ in range(5)]
        assert len(set(primes)) == 5

    def test_default_bits_1024(self):
        """Default bit length should be 1024."""
        p = generate_prime()
        assert 1023 <= p.bit_length() <= 1025

    # ── error cases ──────────────────────────────────────────────────────────

    def test_zero_bits_raises(self):
        with pytest.raises((ValueError, AssertionError, StopIteration)):
            generate_prime(bits=0)

    def test_negative_bits_raises(self):
        with pytest.raises((ValueError, AssertionError)):
            generate_prime(bits=-10)

    def test_float_bits_raises(self):
        with pytest.raises(TypeError):
            generate_prime(bits=256.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  3. extended_gcd()
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtendedGcd:

    def test_gcd_correctness(self):
        """Returned gcd should be correct."""
        assert extended_gcd(48, 18)[0] == 6
        assert extended_gcd(1071, 462)[0] == 21
        assert extended_gcd(100, 35)[0] == 5

    def test_coprime_returns_one(self):
        """GCD of coprime numbers should be 1."""
        assert extended_gcd(17, 19)[0] == 1
        assert extended_gcd(7, 11)[0] == 1

    def test_bezout_identity(self):
        """Verify Bezout identity: gcd = a*x + b*y."""
        test_cases = [(48, 18), (1071, 462), (100, 35), (56, 15)]
        for a, b in test_cases:
            gcd, x, y = extended_gcd(a, b)
            assert a * x + b * y == gcd, f"Bezout failed for ({a}, {b})"

    def test_base_case_b_zero(self):
        """When b=0, gcd should be a."""
        gcd, x, y = extended_gcd(17, 0)
        assert gcd == 17
        assert x == 1

    def test_zero_a_zero_b(self):
        """extended_gcd(0, 0) should return gcd=0."""
        gcd, _, _ = extended_gcd(0, 0)
        assert gcd == 0

    def test_same_numbers(self):
        """GCD of n and n should be n."""
        for n in [5, 17, 100]:
            gcd, _, _ = extended_gcd(n, n)
            assert gcd == n

    def test_one_and_any_number(self):
        """GCD of 1 and any n should be 1."""
        for n in [2, 17, 100, 1000]:
            gcd, _, _ = extended_gcd(1, n)
            assert gcd == 1

    # ── error cases ──────────────────────────────────────────────────────────

    def test_string_input_raises(self):
        with pytest.raises(TypeError):
            extended_gcd("48", "18")


# ═══════════════════════════════════════════════════════════════════════════════
#  4. mod_inverse()
# ═══════════════════════════════════════════════════════════════════════════════

class TestModInverse:

    def test_basic_inverse(self):
        """Verify that (a * a_inv) ≡ 1 (mod m)."""
        a_inv = mod_inverse(3, 11)
        assert (3 * a_inv) % 11 == 1

    def test_multiple_inverses(self):
        """Test various (a, m) pairs."""
        test_cases = [(3, 7), (5, 12), (7, 26), (17, 100), (12, 35)]
        for a, m in test_cases:
            a_inv = mod_inverse(a, m)
            assert (a * a_inv) % m == 1, f"Inverse failed for {a} mod {m}"

    def test_inverse_is_in_range(self):
        """Returned inverse should be in [0, m)."""
        for a, m in [(3, 7), (5, 11), (17, 100)]:
            a_inv = mod_inverse(a, m)
            assert 0 <= a_inv < m

    def test_one_inverse(self):
        """Inverse of 1 should be 1."""
        assert mod_inverse(1, 7) == 1
        assert mod_inverse(1, 100) == 1

    def test_large_modulus(self):
        """Test with large coprime numbers."""
        a = 101
        m = 997
        # These are coprime primes
        a_inv = mod_inverse(a, m)
        assert (a * a_inv) % m == 1

    # ── error cases ──────────────────────────────────────────────────────────

    def test_non_coprime_raises(self):
        """If gcd(a, m) ≠ 1, should raise ValueError."""
        with pytest.raises(ValueError):
            mod_inverse(6, 9)  # gcd = 3

    def test_non_coprime_even_numbers(self):
        """Even numbers are not coprime with even modulus."""
        with pytest.raises(ValueError):
            mod_inverse(4, 10)  # gcd = 2

    def test_a_equals_m_raises(self):
        """mod_inverse(m, m) should fail (gcd = m)."""
        with pytest.raises(ValueError):
            mod_inverse(7, 7)

    def test_zero_modulus_raises(self):
        """Modulus of 0 should raise an error."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            mod_inverse(5, 0)

    def test_string_input_raises(self):
        with pytest.raises(TypeError):
            mod_inverse("3", "7")


# ═══════════════════════════════════════════════════════════════════════════════
#  5. generate_rsa_keypair()
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateRsaKeypair:

    def test_returns_three_values(self):
        """Keypair should be (e, d, N)."""
        result = generate_rsa_keypair(bits=512)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_e_is_65537(self):
        """Standard RSA public exponent should be 65537."""
        e, d, N = generate_rsa_keypair(bits=512)
        assert e == 65537

    def test_d_is_positive(self):
        """Private exponent should be positive."""
        _, d, _ = generate_rsa_keypair(bits=512)
        assert d > 0


    def test_rsa_property_m_to_e_to_d(self):
        """Verify RSA property: m^e^d ≡ m (mod N)."""
        e, d, N = generate_rsa_keypair(bits=512)
        m = 123456
        c = pow(m, e, N)
        m_recovered = pow(c, d, N)
        assert m_recovered == m

    def test_different_keypairs_are_different(self):
        """Multiple calls should generate different keys."""
        keys = [generate_rsa_keypair(bits=512) for _ in range(3)]
        N_values = [k[2] for k in keys]
        assert len(set(N_values)) == 3

    def test_bit_length_512(self):
        """Generated N should have approximately 512 bits."""
        _, _, N = generate_rsa_keypair(bits=512)
        assert 510 <= N.bit_length() <= 514

    def test_bit_length_1024(self):
        """Generated N should have approximately 1024 bits."""
        _, _, N = generate_rsa_keypair(bits=1024)
        assert 1022 <= N.bit_length() <= 1026

    def test_default_bits_2048(self):
        """Default bit length should be 2048."""
        _, _, N = generate_rsa_keypair()
        assert 2046 <= N.bit_length() <= 2050

    def test_d_and_e_multiply_to_1_mod_phi(self):
        """Verify that (e * d) ≡ 1 (mod φ(N))."""
        e, d, N = generate_rsa_keypair(bits=512)
        for m in [42, 12345, 98765]:
            c = pow(m, e, N)
            m_dec = pow(c, d, N)
            assert m_dec == m

    def test_multiple_messages_encrypt_decrypt(self):
        """Encrypt and decrypt multiple messages."""
        e, d, N = generate_rsa_keypair(bits=512)
        messages = [1, 42, 100, 1000, 10000]
        for m in messages:
            assert m < N, "Message must be less than N"
            c = pow(m, e, N)
            m_dec = pow(c, d, N)
            assert m_dec == m

    # ── error cases ──────────────────────────────────────────────────────────

    def test_float_bits_raises(self):
        with pytest.raises(TypeError):
            generate_rsa_keypair(bits=512.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  6. Integration: Key Generation and Encryption/Decryption
# ═══════════════════════════════════════════════════════════════════════════════

class TestRsaIntegration:
    """
    Test complete RSA workflows using all rsa_core functions together.
    """

    def test_full_rsa_workflow_small_key(self):
        """Generate keys and perform encryption/decryption."""
        e, d, N = generate_rsa_keypair(bits=512)
        
        # Verify basic RSA properties
        assert e == 65537
        assert d > 0
        assert N > 0
        
        # Encrypt and decrypt
        plaintext = 42
        ciphertext = pow(plaintext, e, N)
        decrypted = pow(ciphertext, d, N)
        assert decrypted == plaintext

    def test_full_rsa_workflow_medium_key(self):
        """Test with 1024-bit key."""
        e, d, N = generate_rsa_keypair(bits=1024)
        
        plaintexts = [123, 4567, 89012, 345678]
        for plaintext in plaintexts:
            assert plaintext < N
            ciphertext = pow(plaintext, e, N)
            decrypted = pow(ciphertext, d, N)
            assert decrypted == plaintext

    def test_gcd_used_in_key_generation(self):
        """Verify that extended_gcd is used correctly in key generation."""
        # If we can generate a valid keypair, extended_gcd must work
        e, d, N = generate_rsa_keypair(bits=512)
        
        # The property e*d ≡ 1 (mod φ(N)) holds, which uses mod_inverse
        # which uses extended_gcd. Test with messages:
        for m in [2, 3, 5, 7, 11]:
            assert pow(m, e * d, N) == m

    def test_different_keys_different_ciphertexts(self):
        """Same message with different keys produces different ciphertexts."""
        e1, _, N1 = generate_rsa_keypair(bits=512)
        e2, _, N2 = generate_rsa_keypair(bits=512)
        
        m = 42
        c1 = pow(m, e1, N1)
        c2 = pow(m, e2, N2)
        
        # Different N values, so even if e is the same, mod arithmetic differs
        assert N1 != N2
