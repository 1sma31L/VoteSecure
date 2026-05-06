"""
test_commissioner.py — pytest test suite for commissioner.py

Run with:  pytest test_commissioner.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "entities"))

from commissioner import Commissioner


# ═══════════════════════════════════════════════════════════════════════════════
#  Commissioner.__init__()
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommissionerInit:

    def test_creates_empty_valid_n1_codes(self):
        """Initialize should create empty N1 codes set."""
        commissioner = Commissioner()
        assert hasattr(commissioner, 'valid_n1_codes')
        assert isinstance(commissioner.valid_n1_codes, set)
        assert len(commissioner.valid_n1_codes) == 0

    def test_creates_empty_valid_n2_hashes(self):
        """Initialize should create empty N2 hashes set."""
        commissioner = Commissioner()
        assert hasattr(commissioner, 'valid_n2_hashes')
        assert isinstance(commissioner.valid_n2_hashes, set)
        assert len(commissioner.valid_n2_hashes) == 0

    def test_multiple_instances_independent(self):
        """Each Commissioner instance should be independent."""
        c1 = Commissioner()
        c2 = Commissioner()
        assert c1.valid_n1_codes is not c2.valid_n1_codes
        assert c1.valid_n2_hashes is not c2.valid_n2_hashes


# ═══════════════════════════════════════════════════════════════════════════════
#  Commissioner.register_voter()
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegisterVoter:

    def test_register_single_voter(self):
        """Register one voter with N1 and N2 hash."""
        commissioner = Commissioner()
        commissioner.register_voter("ABC123XYZ789", "hash_n2_voter1")
        
        assert "ABC123XYZ789" in commissioner.valid_n1_codes
        assert "hash_n2_voter1" in commissioner.valid_n2_hashes

    def test_register_multiple_voters(self):
        """Register multiple voters."""
        commissioner = Commissioner()
        voters = [
            ("N1_001", "hash_001"),
            ("N1_002", "hash_002"),
            ("N1_003", "hash_003"),
        ]
        
        for n1, n2_hash in voters:
            commissioner.register_voter(n1, n2_hash)
        
        assert len(commissioner.valid_n1_codes) == 3
        assert len(commissioner.valid_n2_hashes) == 3
        
        for n1, n2_hash in voters:
            assert n1 in commissioner.valid_n1_codes
            assert n2_hash in commissioner.valid_n2_hashes

    def test_duplicate_n1_does_not_duplicate_in_set(self):
        """Registering same N1 twice should only appear once (set property)."""
        commissioner = Commissioner()
        commissioner.register_voter("SAME_N1", "hash1")
        commissioner.register_voter("SAME_N1", "hash2")
        
        # Set deduplicates
        assert len(commissioner.valid_n1_codes) == 1
        assert "SAME_N1" in commissioner.valid_n1_codes

    def test_duplicate_n2_hash_does_not_duplicate(self):
        """Registering same N2 hash twice should only appear once."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_A", "SAME_HASH")
        commissioner.register_voter("N1_B", "SAME_HASH")
        
        assert len(commissioner.valid_n2_hashes) == 1
        assert "SAME_HASH" in commissioner.valid_n2_hashes

    def test_register_empty_strings(self):
        """Should allow registration of empty strings (no validation in __init__)."""
        commissioner = Commissioner()
        commissioner.register_voter("", "")
        assert "" in commissioner.valid_n1_codes
        assert "" in commissioner.valid_n2_hashes

    def test_register_special_characters(self):
        """Should allow special characters in N1 and N2 hash."""
        commissioner = Commissioner()
        commissioner.register_voter("N1!@#$%", "hash!@#$%")
        assert "N1!@#$%" in commissioner.valid_n1_codes
        assert "hash!@#$%" in commissioner.valid_n2_hashes

    def test_register_numeric_strings(self):
        """Should handle numeric strings."""
        commissioner = Commissioner()
        commissioner.register_voter("123456", "789012")
        assert "123456" in commissioner.valid_n1_codes
        assert "789012" in commissioner.valid_n2_hashes

    def test_register_accepts_any_type(self):
        """Commissioner accepts any hashable type (no validation)."""
        commissioner = Commissioner()
        # Sets require hashable objects, so integers work too
        commissioner.register_voter(123, 456)
        assert 123 in commissioner.valid_n1_codes
        assert 456 in commissioner.valid_n2_hashes


# ═══════════════════════════════════════════════════════════════════════════════
#  Commissioner.validate_n1()
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateN1:

    def test_validate_registered_n1_returns_true(self):
        """validate_n1() should return True for registered N1."""
        commissioner = Commissioner()
        commissioner.register_voter("VALID_N1", "hash")
        assert commissioner.validate_n1("VALID_N1") is True

    def test_validate_unregistered_n1_returns_false(self):
        """validate_n1() should return False for unregistered N1."""
        commissioner = Commissioner()
        assert commissioner.validate_n1("INVALID_N1") is False

    def test_validate_case_sensitive(self):
        """N1 validation should be case-sensitive."""
        commissioner = Commissioner()
        commissioner.register_voter("AbC123", "hash")
        assert commissioner.validate_n1("AbC123") is True
        assert commissioner.validate_n1("abc123") is False
        assert commissioner.validate_n1("ABC123") is False

    def test_validate_does_not_consume(self):
        """validate_n1() should NOT remove N1 from the set."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_TEST", "hash")
        
        commissioner.validate_n1("N1_TEST")
        # Still valid after validation
        assert commissioner.validate_n1("N1_TEST") is True
        assert "N1_TEST" in commissioner.valid_n1_codes

    def test_validate_multiple_calls_same_result(self):
        """Multiple validate_n1() calls on same N1 should return same result."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_MULTI", "hash")
        
        r1 = commissioner.validate_n1("N1_MULTI")
        r2 = commissioner.validate_n1("N1_MULTI")
        r3 = commissioner.validate_n1("N1_MULTI")
        
        assert r1 == r2 == r3 == True

    def test_validate_after_consume(self):
        """After consume_n1(), validate_n1() should return False."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_CONSUME", "hash")
        
        assert commissioner.validate_n1("N1_CONSUME") is True
        commissioner.consume_n1("N1_CONSUME")
        assert commissioner.validate_n1("N1_CONSUME") is False

    # ── error cases ──────────────────────────────────────────────────────────

    def test_validate_none_returns_false(self):
        """validate_n1(None) should return False."""
        commissioner = Commissioner()
        assert commissioner.validate_n1(None) is False

    def test_validate_integer_returns_false(self):
        """validate_n1() with integer should return False (not found)."""
        commissioner = Commissioner()
        # Integers not in the set, so False
        assert commissioner.validate_n1(123) is False

    def test_validate_empty_string(self):
        """Validate empty string (not registered) should return False."""
        commissioner = Commissioner()
        assert commissioner.validate_n1("") is False


# ═══════════════════════════════════════════════════════════════════════════════
#  Commissioner.consume_n1()
# ═══════════════════════════════════════════════════════════════════════════════

class TestConsumeN1:

    def test_consume_registered_n1_returns_true(self):
        """consume_n1() should return True for registered N1."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_CONSUME", "hash")
        assert commissioner.consume_n1("N1_CONSUME") is True

    def test_consume_unregistered_n1_returns_false(self):
        """consume_n1() should return False for unregistered N1."""
        commissioner = Commissioner()
        assert commissioner.consume_n1("UNREGISTERED") is False

    def test_consume_removes_n1(self):
        """consume_n1() should remove N1 from valid_n1_codes."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_REMOVE", "hash")
        
        assert "N1_REMOVE" in commissioner.valid_n1_codes
        commissioner.consume_n1("N1_REMOVE")
        assert "N1_REMOVE" not in commissioner.valid_n1_codes

    def test_consume_twice_returns_false_second_time(self):
        """Consuming same N1 twice: first True, second False."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_TWICE", "hash")
        
        assert commissioner.consume_n1("N1_TWICE") is True
        assert commissioner.consume_n1("N1_TWICE") is False

    def test_consume_multiple_n1s(self):
        """Consume multiple N1s in sequence."""
        commissioner = Commissioner()
        n1_codes = ["N1_001", "N1_002", "N1_003"]
        
        for n1 in n1_codes:
            commissioner.register_voter(n1, f"hash_{n1}")
        
        for n1 in n1_codes:
            assert commissioner.consume_n1(n1) is True
        
        assert len(commissioner.valid_n1_codes) == 0

    def test_consume_does_not_affect_n2_hashes(self):
        """Consuming N1 should not affect N2 hashes."""
        commissioner = Commissioner()
        commissioner.register_voter("N1_TEST", "hash_test")
        
        commissioner.consume_n1("N1_TEST")
        
        assert len(commissioner.valid_n2_hashes) == 1
        assert "hash_test" in commissioner.valid_n2_hashes

    def test_consume_case_sensitive(self):
        """consume_n1() should be case-sensitive."""
        commissioner = Commissioner()
        commissioner.register_voter("CasE_N1", "hash")
        
        assert commissioner.consume_n1("case_n1") is False
        # Original still in set
        assert "CasE_N1" in commissioner.valid_n1_codes

    # ── error cases ──────────────────────────────────────────────────────────

    def test_consume_none_returns_false(self):
        """consume_n1(None) should return False."""
        commissioner = Commissioner()
        assert commissioner.consume_n1(None) is False

    def test_consume_integer_returns_false(self):
        """consume_n1() with integer should return False."""
        commissioner = Commissioner()
        assert commissioner.consume_n1(123) is False

    def test_consume_empty_string_returns_false(self):
        """consume_n1('') should return False (not registered)."""
        commissioner = Commissioner()
        assert commissioner.consume_n1("") is False


# ═══════════════════════════════════════════════════════════════════════════════
#  Commissioner.register_n2_hash()
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegisterN2Hash:

    def test_register_single_n2_hash(self):
        """Register a single N2 hash."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("hash_n2_001")
        
        assert "hash_n2_001" in commissioner.valid_n2_hashes

    def test_register_multiple_n2_hashes(self):
        """Register multiple N2 hashes."""
        commissioner = Commissioner()
        hashes = ["hash_001", "hash_002", "hash_003"]
        
        for h in hashes:
            commissioner.register_n2_hash(h)
        
        assert len(commissioner.valid_n2_hashes) == 3
        for h in hashes:
            assert h in commissioner.valid_n2_hashes

    def test_register_duplicate_n2_hash(self):
        """Registering duplicate N2 hash should not duplicate in set."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("DUPLICATE")
        commissioner.register_n2_hash("DUPLICATE")
        
        assert len(commissioner.valid_n2_hashes) == 1
        assert "DUPLICATE" in commissioner.valid_n2_hashes

    def test_register_n2_hash_independent_of_n1(self):
        """register_n2_hash() should work independently of N1 codes."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("hash_only")
        
        # No N1 codes registered
        assert len(commissioner.valid_n1_codes) == 0
        assert "hash_only" in commissioner.valid_n2_hashes

    def test_register_n2_hash_empty_string(self):
        """Should allow empty string as N2 hash."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("")
        assert "" in commissioner.valid_n2_hashes

    def test_register_n2_hash_accepts_any_type(self):
        """N2 hash registration accepts any hashable type (no validation)."""
        commissioner = Commissioner()
        commissioner.register_n2_hash(123)
        assert 123 in commissioner.valid_n2_hashes


# ═══════════════════════════════════════════════════════════════════════════════
#  Commissioner.verify_n2_hash()
# ═══════════════════════════════════════════════════════════════════════════════

class TestVerifyN2Hash:

    def test_verify_registered_n2_hash_returns_true(self):
        """verify_n2_hash() should return True for registered hash."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("hash_verified")
        assert commissioner.verify_n2_hash("hash_verified") is True

    def test_verify_unregistered_n2_hash_returns_false(self):
        """verify_n2_hash() should return False for unregistered hash."""
        commissioner = Commissioner()
        assert commissioner.verify_n2_hash("unregistered") is False

    def test_verify_case_sensitive(self):
        """verify_n2_hash() should be case-sensitive."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("HashTest")
        assert commissioner.verify_n2_hash("HashTest") is True
        assert commissioner.verify_n2_hash("hashtest") is False

    def test_verify_does_not_remove_hash(self):
        """verify_n2_hash() should NOT remove the hash from the set."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("hash_persist")
        
        commissioner.verify_n2_hash("hash_persist")
        # Still there
        assert "hash_persist" in commissioner.valid_n2_hashes
        assert commissioner.verify_n2_hash("hash_persist") is True

    def test_verify_multiple_calls(self):
        """Multiple verify_n2_hash() calls should return same result."""
        commissioner = Commissioner()
        commissioner.register_n2_hash("hash_multi")
        
        r1 = commissioner.verify_n2_hash("hash_multi")
        r2 = commissioner.verify_n2_hash("hash_multi")
        r3 = commissioner.verify_n2_hash("hash_multi")
        
        assert r1 == r2 == r3 == True

    # ── error cases ──────────────────────────────────────────────────────────

    def test_verify_none_returns_false(self):
        """verify_n2_hash(None) should return False."""
        commissioner = Commissioner()
        assert commissioner.verify_n2_hash(None) is False

    def test_verify_integer_returns_false(self):
        """verify_n2_hash() with integer should return False."""
        commissioner = Commissioner()
        assert commissioner.verify_n2_hash(123) is False

    def test_verify_empty_string(self):
        """Verify empty string (not registered) should return False."""
        commissioner = Commissioner()
        assert commissioner.verify_n2_hash("") is False


# ═══════════════════════════════════════════════════════════════════════════════
#  Integration: Complete Voting Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommissionerIntegration:
    """
    Test complete voting workflows with Commissioner.
    """

    def test_single_voter_lifecycle(self):
        """Register, validate, verify, and consume a single voter."""
        commissioner = Commissioner()
        n1 = "VOTER_N1_001"
        n2_hash = "hash_voter_001"
        
        # Register
        commissioner.register_voter(n1, n2_hash)
        
        # Validate N1
        assert commissioner.validate_n1(n1) is True
        
        # Verify N2 hash
        assert commissioner.verify_n2_hash(n2_hash) is True
        
        # Consume N1 (vote cast)
        assert commissioner.consume_n1(n1) is True
        
        # N1 should now be invalid
        assert commissioner.validate_n1(n1) is False
        
        # N2 hash should still be valid
        assert commissioner.verify_n2_hash(n2_hash) is True

    def test_multiple_voters_independent(self):
        """Multiple voters with independent N1 and N2 hashes."""
        commissioner = Commissioner()
        voters = [
            ("N1_001", "hash_001"),
            ("N1_002", "hash_002"),
            ("N1_003", "hash_003"),
        ]
        
        # Register all
        for n1, n2_hash in voters:
            commissioner.register_voter(n1, n2_hash)
        
        # Validate all before consumption
        for n1, n2_hash in voters:
            assert commissioner.validate_n1(n1) is True
            assert commissioner.verify_n2_hash(n2_hash) is True
        
        # Consume voters 1 and 3
        assert commissioner.consume_n1("N1_001") is True
        assert commissioner.consume_n1("N1_003") is True
        
        # Voter 2 should still be valid, others invalid
        assert commissioner.validate_n1("N1_001") is False
        assert commissioner.validate_n1("N1_002") is True
        assert commissioner.validate_n1("N1_003") is False

    def test_voter_attempts_double_voting(self):
        """Attempt to vote twice with same N1 should fail on second."""
        commissioner = Commissioner()
        n1 = "DOUBLE_VOTER_N1"
        n2_hash = "double_voter_hash"
        
        commissioner.register_voter(n1, n2_hash)
        
        # First vote succeeds
        assert commissioner.consume_n1(n1) is True
        
        # Second attempt with same N1 fails
        assert commissioner.consume_n1(n1) is False

    def test_separate_n1_and_n2_registration(self):
        """N1 and N2 hashes can be registered separately."""
        commissioner = Commissioner()
        
        # Register N1s
        for i in range(5):
            commissioner.register_voter(f"N1_{i}", f"hash_{i}")
        
        # Register additional N2 hashes separately
        for i in range(5, 8):
            commissioner.register_n2_hash(f"hash_{i}")
        
        assert len(commissioner.valid_n1_codes) == 5
        assert len(commissioner.valid_n2_hashes) == 8

    def test_election_results_tracking(self):
        """Track votes through consume operations."""
        commissioner = Commissioner()
        num_voters = 10
        
        # Register all voters
        for i in range(num_voters):
            commissioner.register_voter(f"N1_{i:03d}", f"hash_{i:03d}")
        
        # Simulate 7 voters voting
        votes_cast = 0
        for i in range(7):
            if commissioner.consume_n1(f"N1_{i:03d}"):
                votes_cast += 1
        
        # 3 voters didn't vote
        assert votes_cast == 7
        assert len(commissioner.valid_n1_codes) == 3
