# administrator.py
# Compatible with:
#   blind_sign.py → sign_blind(m_masked, d, N)
#   rsa_utils.py  → rsa_verify(m, s, e, N)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'crypto'))

from blind_sign import sign_blind
from rsa_utils  import rsa_verify


class Administrator:
    def __init__(
        self,
        pub_key:  tuple,  
        priv_key: tuple,   
        commissioner,      
    ):
       
        self.e, self.N = pub_key
        self.d, _      = priv_key          

        self.pub_key     = pub_key         
        self.commissioner = commissioner

        self._signed_voters = set()        

    # ------------------------------------------------------------------ #
    #  Step 1 — Verify voter eligibility                                   #
    # ------------------------------------------------------------------ #
    def verify_voter(self, N1: str) -> bool:
        """
        Ask the commissioner whether N1 is on the valid list.
        Returns True if eligible, False otherwise.
        """
        return self.commissioner.is_valid_N1(N1)

    # ------------------------------------------------------------------ #
    #  Step 2 — Blind signature                                            #
    # ------------------------------------------------------------------ #
    def sign(self, m_masked: int) -> int:
      
        if not (0 <= m_masked < self.N):
            raise ValueError(
                f"Masked ballot {m_masked} out of RSA range [0, {self.N - 1}]."
            )
        return sign_blind(m_masked, self.d, self.N)

    # ------------------------------------------------------------------ #
    #  Step 3 — Full signing request                                       #
    # ------------------------------------------------------------------ #
    def process_request(self, N1: str, m_masked: int) -> int:
       
      
        if N1 in self._signed_voters:
            raise PermissionError(
                f"Voter N1={N1!r} has already received a signature."
            )

       
        if not self.verify_voter(N1):
            raise PermissionError(
                f"Voter N1={N1!r} is not recognised by the commissioner."
            )

      
        s_blind = self.sign(m_masked)

        
        self._signed_voters.add(N1)

        return s_blind

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #
    def get_public_key(self) -> tuple:
       
        return self.pub_key

    def __repr__(self):
        return (
            f"Administrator(e={self.e}, N={self.N}, "
            f"signed_voters={len(self._signed_voters)})"
        )
