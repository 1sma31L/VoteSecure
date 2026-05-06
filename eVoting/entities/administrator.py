from crypto.rsa_core import generate_rsa_keypair
from crypto.blind_signature import sign_blind


class Administrator:
    
    def __init__(self):
        self.e_A = None
        self.d_A = None
        self.N_A = None

        # N1 codes that are allowed to vote
        self._eligible_n1 = set()
        # N1 codes that have already received a signature from us
        # we use this to make sure nobody votes twice
        self._used_n1 = set()
        # optional link to the Commissioner for eligibility checks
        self._commissioner = None

    def setup_keys(self, bits=2048):
        # Generate our RSA key pair at the start of the election
        # The public key (e_A, N_A) gets shared with everyone
        # d_A never leaves this object
        self.e_A, self.d_A, self.N_A = generate_rsa_keypair(bits=bits)
        print("Administrator keys generated,", bits, "bits")
        return {"e_A": self.e_A, "N_A": self.N_A}

    def set_commissioner(self, commissioner):
        # If we have a commissioner linked, we ask it to validate N1 codes
        # instead of checking our own internal list
        self._commissioner = commissioner

    def register_eligible_n1(self, n1_code):
        # Add a valid N1 code to our list
        # This is used when no commissioner is linked (mostly for testing)
        self._eligible_n1.add(n1_code)

    def get_public_key(self):
        if self.e_A is None:
            raise RuntimeError("Keys have not been generated yet, call setup_keys first.")
        return {"e_A": self.e_A, "N_A": self.N_A}

    def verify_voter_eligibility(self, n1_code):
        # Check two things:
        # 1. Is this N1 actually registered as a valid voter
        # 2. Has this N1 already been used to get a signature (double vote check)

        if self._commissioner is not None:
            eligible = self._commissioner.validate_n1(n1_code)
        else:
            eligible = n1_code in self._eligible_n1

        if not eligible:
            print("Rejected N1", n1_code, "- not in the eligible list")
            return False

        if n1_code in self._used_n1:
            print("Rejected N1", n1_code, "- this voter already voted")
            return False

        return True

    def sign_blinded_vote(self, m_masked, n1_code):
        # This is called when a voter sends us their blinded vote and N1 code
        # We check the N1, then sign the masked message
        # We mark the N1 as used right away before signing to avoid any issues
        # We return the blind signature back to the voter who will then unblind it

        if self.d_A is None:
            raise RuntimeError("Keys not set up yet, call setup_keys first.")

        if not self.verify_voter_eligibility(n1_code):
            return None

        # Mark N1 as used before signing
        self._used_n1.add(n1_code)

        s_blind = sign_blind(m_masked, self.d_A, self.N_A)
        print("Signed blind vote for voter with N1:", n1_code)
        return s_blind

    def __repr__(self):
        status = "keys ready" if self.e_A else "no keys"
        return "Administrator [" + status + "] - " + str(len(self._used_n1)) + " votes signed so far"


# if __name__ == "__main__":
#     from crypto.blind_signature import blind_message, unblind_signature
#     from crypto.rsa_ops import rsa_verify

#     admin = Administrator()
#     pub = admin.setup_keys(bits=512)
#     e_A = pub["e_A"]
#     N_A = pub["N_A"]

#     admin.register_eligible_n1("N1-ALICE")
#     admin.register_eligible_n1("N1-BOB")

#     print("\nTesting with voter ALICE")
#     m_alice = 99991 % N_A

#     m_masked, k = blind_message(m_alice, e_A, N_A)
#     print("Alice sends blinded vote and N1 to administrator")

#     s_blind = admin.sign_blinded_vote(m_masked, "N1-ALICE")
#     assert s_blind is not None

#     signature = unblind_signature(s_blind, k, N_A)
#     assert rsa_verify(m_alice, signature, e_A, N_A), "Signature check failed"
#     print("Alice unblinds and verifies her signature - works correctly")

#     print("\nTesting double vote attempt by ALICE")
#     s2 = admin.sign_blinded_vote(m_masked, "N1-ALICE")
#     assert s2 is None
#     print("Double vote correctly rejected")

#     print("\nTesting unknown voter")
#     s3 = admin.sign_blinded_vote(m_masked, "N1-FAKE")
#     assert s3 is None
#     print("Unknown voter correctly rejected")

#     print("\nAll tests passed")
#     print(admin)
