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

