# voter.py
# Compatible with:
#   blind_sign.py → blind_message(m, e, N), unblind_signature(s, k, N)
#   rsa_utils.py  → rsa_encrypt(m, e, N),   rsa_verify(m, s, e, N)
#   encoding.py   → encode_vote(vote, N2, rsa_modulus)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'crypto'))

from blind_sign import blind_message, unblind_signature
from rsa_utils  import rsa_encrypt, rsa_verify
from encoding   import encode_vote


class Voter:
    def __init__(
        self,
        N1: str,
        N2: str,
        admin_pub_key:   tuple,   
        counter_pub_key: tuple,  
    ):
    
        self.N1 = N1
        self.N2 = N2

        self.e_admin,   self.N_admin   = admin_pub_key
        self.e_counter, self.N_counter = counter_pub_key

        self.k         = None   
        self.has_voted = False  

    # ------------------------------------------------------------------ #
    #  Step 1 — Encode ballot to integer                                   #
    # ------------------------------------------------------------------ #
    def encode_ballot(self, vote: int) -> int:
        """
        Combine (vote, N2) into a single RSA-safe integer using
        encoding.encode_vote().

        The result is guaranteed to be in [1, N_admin - 1].
        """
        return encode_vote(vote, self.N2, rsa_modulus=self.N_admin)

    # ------------------------------------------------------------------ #
    #  Step 2 — Blind the ballot                                           #
    # ------------------------------------------------------------------ #
    def blind_ballot(self, m: int) -> int:
       
        m_masked, k = blind_message(m, self.e_admin, self.N_admin)
        self.k = k
        return m_masked

    # ------------------------------------------------------------------ #
    #  Step 3 — Unblind the administrator's signature                      #
    # ------------------------------------------------------------------ #
    def unblind(self, s_blind: int) -> int:
       
        if self.k is None:
            raise RuntimeError("No blinding factor — call blind_ballot() first.")
        return unblind_signature(s_blind, self.k, self.N_admin)

    # ------------------------------------------------------------------ #
    #  Step 4 — Verify own signature (self-check before submitting)        #
    # ------------------------------------------------------------------ #
    def verify_signature(self, m: int, s: int) -> bool:
       
        return rsa_verify(m, s, self.e_admin, self.N_admin)

    # ------------------------------------------------------------------ #
    #  Step 5 — Encrypt raw score for the counter                          #
    # ------------------------------------------------------------------ #
    def encrypt_vote(self, vote: int) -> int:
      
        if not (0 < vote < self.N_counter):
            raise ValueError(
                f"vote={vote} out of counter RSA range [1, {self.N_counter - 1}]."
            )
        return rsa_encrypt(vote, self.e_counter, self.N_counter)

    # ------------------------------------------------------------------ #
    #  Step 6 — Full voting process                                        #
    # ------------------------------------------------------------------ #
    def vote(self, vote_value: int, administrator) -> dict:
      
        
      
        if self.has_voted:
            raise RuntimeError("This voter has already cast a ballot.")

        m = self.encode_ballot(vote_value)

       
        m_prime = self.blind_ballot(m)

        s_blind = administrator.process_request(self.N1, m_prime)

        signature = self.unblind(s_blind)

        if not self.verify_signature(m, signature):
            raise ValueError(
                "Signature verification failed — unblinded signature is invalid."
            )
        encrypted_vote = self.encrypt_vote(vote_value)

        
        self.has_voted = True

        return {
            "N1"            : self.N1,
            "ballot"        : m,
            "encrypted_vote": encrypted_vote,
            "signature"     : signature,
            "N2"            : self.N2,
        }

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #
    def __repr__(self):
        return (
            f"Voter(N1={self.N1!r}, N2={self.N2!r}, "
            f"has_voted={self.has_voted})"
        )
