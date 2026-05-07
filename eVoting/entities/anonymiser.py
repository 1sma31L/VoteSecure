
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'crypto'))


class Anonymiser:
    def __init__(self, commissioner):
       
        self.commissioner = commissioner

        
        self._ballot_box = []

        self.voting_open = True   

    # ------------------------------------------------------------------ #
    #  Step 1 — Receive vote from voter                                    #
    # ------------------------------------------------------------------ #
    def receive_vote(self, payload: dict) -> bool:
      
      
        if not self.voting_open:
            raise RuntimeError("Voting period is closed. No more votes accepted.")

        required = {"N1", "encrypted_vote", "signature", "ballot", "N2"}
        missing  = required - payload.keys()
        if missing:
            raise KeyError(f"Missing fields in payload: {missing}")

        N1 = payload["N1"]

        if not self.commissioner.is_valid_N1(N1):
            raise PermissionError(
                f"Vote rejected: N1={N1!r} is not valid or has already been used."
            )

        self.commissioner.invalidate_N1(N1)

        anonymous_ballot = {
            "encrypted_vote": payload["encrypted_vote"],
            "signature"     : payload["signature"],
            "ballot"        : payload["ballot"],
            "N2"            : payload["N2"],
        }
        self._ballot_box.append(anonymous_ballot)

        return True

    # ------------------------------------------------------------------ #
    #  Step 2 — Strip identity (explicit utility)                          #
    # ------------------------------------------------------------------ #
    def strip_identity(self, payload: dict) -> dict:
   
        return {k: v for k, v in payload.items() if k != "N1"}

    # ------------------------------------------------------------------ #
    #  Step 3 — Close voting period                                        #
    # ------------------------------------------------------------------ #
    def close_voting(self):
       
        self.voting_open = False

    # ------------------------------------------------------------------ #
    #  Step 4 — Forward all ballots to decompteur                          #
    # ------------------------------------------------------------------ #
    def forward_to_decompteur(self, decompteur) -> int:
        
        if self.voting_open:
            raise RuntimeError(
                "Cannot forward votes while voting is still open. "
                "Call close_voting() first."
            )

        for ballot in self._ballot_box:
            decompteur.receive_vote(ballot)

        return len(self._ballot_box)

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #
    def ballot_count(self) -> int:
        
        return len(self._ballot_box)

    def __repr__(self):
        return (
            f"Anonymiser("
            f"ballots={len(self._ballot_box)}, "
            f"voting_open={self.voting_open})"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  Self-test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    SEP = "─" * 60

    # ── Stub commissioner ─────────────────────────────────────────────────────
    class StubCommissioner:
        def __init__(self, valid):
            self._valid = set(valid)

        def is_valid_N1(self, N1):
            return N1 in self._valid

        def invalidate_N1(self, N1):
            self._valid.discard(N1)

    # ── Stub decompteur ───────────────────────────────────────────────────────
    class StubDecompteur:
        def __init__(self):
            self.received = []

        def receive_vote(self, ballot):
            self.received.append(ballot)

    # ── Setup ─────────────────────────────────────────────────────────────────
    commissioner = StubCommissioner(["AF15GH258ZQP", "BZ99KL123MNP"])
    anonymiser   = Anonymiser(commissioner)
    decompteur   = StubDecompteur()

    payload1 = {
        "N1"            : "AF15GH258ZQP",
        "encrypted_vote": 512,
        "signature"     : 2981,
        "ballot"        : 948,
        "N2"            : "XY12AB345ZQP",
    }

    payload2 = {
        "N1"            : "BZ99KL123MNP",
        "encrypted_vote": 27,
        "signature"     : 1234,
        "ballot"        : 567,
        "N2"            : "CD56EF789GHI",
    }

    # ── Test 1: receive valid votes ───────────────────────────────────────────
    print(SEP)
    print("1. Receiving valid votes")
    r1 = anonymiser.receive_vote(payload1)
    r2 = anonymiser.receive_vote(payload2)
    assert r1 and r2, "FAIL: valid votes rejected"
    assert anonymiser.ballot_count() == 2, "FAIL: wrong ballot count"
    print(f"   Ballots in box : {anonymiser.ballot_count()}")
    print("   ✓ Both votes accepted")

    # ── Test 2: N1 is stripped ────────────────────────────────────────────────
    print(SEP)
    print("2. Identity stripping")
    stripped = anonymiser.strip_identity(payload1)
    assert "N1" not in stripped,             "FAIL: N1 still present after strip"
    assert "encrypted_vote" in stripped,     "FAIL: encrypted_vote missing"
    assert "signature"      in stripped,     "FAIL: signature missing"
    assert "ballot"         in stripped,     "FAIL: ballot missing"
    assert "N2"             in stripped,     "FAIL: N2 missing"
    print(f"   Stripped payload keys : {list(stripped.keys())}")
    print("   ✓ N1 removed, all other fields preserved")

    # ── Test 3: double vote blocked ───────────────────────────────────────────
    print(SEP)
    print("3. Double-vote guard")
    try:
        anonymiser.receive_vote(payload1)  
        print("   FAIL: double vote was accepted!")
    except PermissionError as e:
        print(f"   Blocked correctly : {e}")
    print("   ✓ Double vote prevented")

    # ── Test 4: invalid N1 blocked ────────────────────────────────────────────
    print(SEP)
    print("4. Invalid N1 guard")
    bad_payload = {**payload1, "N1": "XXXXXXXXXXXX"}
    try:
        anonymiser.receive_vote(bad_payload)
        print("   FAIL: invalid N1 accepted!")
    except PermissionError as e:
        print(f"   Blocked correctly : {e}")
    print("   ✓ Invalid N1 rejected")

    # ── Test 5: cannot forward while voting open ──────────────────────────────
    print(SEP)
    print("5. Forward blocked while voting open")
    try:
        anonymiser.forward_to_decompteur(decompteur)
        print("   FAIL: forward allowed while voting open!")
    except RuntimeError as e:
        print(f"   Blocked correctly : {e}")
    print("   ✓ Forward correctly blocked")

    # ── Test 6: close and forward ─────────────────────────────────────────────
    print(SEP)
    print("6. Close voting and forward to decompteur")
    anonymiser.close_voting()
    count = anonymiser.forward_to_decompteur(decompteur)
    assert count == 2,                  "FAIL: wrong forward count"
    assert len(decompteur.received) == 2, "FAIL: decompteur didn't receive all ballots"
    assert "N1" not in decompteur.received[0], "FAIL: N1 leaked to decompteur!"
    print(f"   Forwarded : {count} ballots")
    print(f"   Decompteur received : {len(decompteur.received)} ballots")
    print(f"   N1 in decompteur ballots : {'N1' in decompteur.received[0]}")
    print("   ✓ Votes forwarded anonymously")

    # ── Test 7: voting closed blocks new votes ────────────────────────────────
    print(SEP)
    print("7. No votes after close")
    try:
        anonymiser.receive_vote({**payload2, "N1": "NEWNEWNEWNEW"})
        print("   FAIL: vote accepted after close!")
    except RuntimeError as e:
        print(f"   Blocked correctly : {e}")
    print("   ✓ Closed period enforced")

    print(SEP)
    print("All tests passed ✓")
    print(SEP)
