from crypto.rsa_core import generate_rsa_keypair
from crypto.rsa_ops import rsa_decrypt, rsa_verify


class Decompteur:

    def __init__(self):
        self.e_D = None
        self.d_D = None
        self.N_D = None

        # all the ballots received from the anonymiser, stored until counting begins
        self._ballot_box = []
        # final results after counting
        self._results = {}
        # link to the commissioner for N2 hash verification during counting
        self._commissioner = None
        # the administrator's public key, needed to verify signatures on ballots
        self._admin_pubkey = None

    def setup_keys(self, bits=2048):
        # Generate the RSA key pair for the decompteur
        # The public key (e_D, N_D) gets published so voters can encrypt their ballots
        # Only we have d_D, so only we can decrypt
        self.e_D, self.d_D, self.N_D = generate_rsa_keypair(bits=bits)
        print("Decompteur keys generated,", bits, "bits")
        return {"e_D": self.e_D, "N_D": self.N_D}

    def set_commissioner(self, commissioner):
        # We need the commissioner during counting to verify that
        # the N2 codes on the ballots are legitimate
        self._commissioner = commissioner

    def set_admin_pubkey(self, e_A, N_A):
        # We need the administrator's public key to verify the signatures on ballots
        # Without this we cannot check if a ballot was actually signed by the admin
        self._admin_pubkey = {"e_A": e_A, "N_A": N_A}

    def get_public_key(self):
        if self.e_D is None:
            raise RuntimeError("Keys not generated yet, call setup_keys first.")
        return {"e_D": self.e_D, "N_D": self.N_D}

    def receive_vote(self, encrypted_vote, signature):
        # Called by the anonymiser to drop a ballot into our box
        # Each ballot contains:
        #   - encrypted_vote: the vote encrypted with our public key
        #   - signature: the administrator's blind signature on the encoded vote
        # N1 is not included here, it was already handled by the anonymiser and commissioner
        # We just store everything and count later when the session is over
        self._ballot_box.append({
            "encrypted_vote": encrypted_vote,
            "signature": signature,
        })
        print("Ballot received, box now has", len(self._ballot_box), "ballots")

    def decrypt_and_count(self, decode_vote_fn=None):
        # This runs after the voting session closes
        # We go through every ballot and do 4 checks before counting it

        if self.d_D is None:
            raise RuntimeError("Call setup_keys before counting.")
        if self._admin_pubkey is None:
            raise RuntimeError("Call set_admin_pubkey before counting.")

        e_A = self._admin_pubkey["e_A"]
        N_A = self._admin_pubkey["N_A"]

        self._results = {}
        valid = 0
        rejected = 0

        print("\nStarting vote count, total ballots:", len(self._ballot_box))

        for i, ballot in enumerate(self._ballot_box):
            enc = ballot["encrypted_vote"]
            sig = ballot["signature"]

            # Step 1: decrypt the ballot with our private key
            try:
                encoded_vote = rsa_decrypt(enc, self.d_D, self.N_D)
            except Exception as ex:
                print("Ballot", i + 1, "rejected - decryption failed:", ex)
                rejected += 1
                continue

            # Step 2: verify the administrator's signature
            # The signature must satisfy sig^e_A mod N_A == encoded_vote
            # If this fails it means the ballot was not signed by the real administrator
            if not rsa_verify(encoded_vote, sig, e_A, N_A):
                print("Ballot", i + 1, "rejected - administrator signature is not valid")
                rejected += 1
                continue

            # Step 3: extract the vote and N2, then verify N2 with the commissioner
            # decode_vote_fn is provided by M5, it takes the encoded integer and
            # returns the actual vote choice and the N2 code
            if decode_vote_fn is not None:
                try:
                    vote_choice, n2 = decode_vote_fn(encoded_vote)
                except Exception as ex:
                    print("Ballot", i + 1, "rejected - could not decode:", ex)
                    rejected += 1
                    continue

                if self._commissioner is not None:
                    if not self._commissioner.verify_n2_hash(n2):
                        print("Ballot", i + 1, "rejected - N2 hash not in the valid list")
                        rejected += 1
                        continue
            else:
                # No decoder available, use raw value as the vote key
                # This happens in testing when M5 is not integrated yet
                vote_choice = encoded_vote

            # Step 4: everything checked out, count the vote
            self._results[vote_choice] = self._results.get(vote_choice, 0) + 1
            valid += 1
            print("Ballot", i + 1, "counted, vote =", vote_choice)

        print("\nCounting done. Valid:", valid, "| Rejected:", rejected)
        return self._results

    def return_results(self):
        # Returns the final tally after counting is done
        if not self._results:
            print("No results yet, call decrypt_and_count first.")
        return self._results

    def __repr__(self):
        status = "keys ready" if self.e_D else "no keys"
        return "Decompteur [" + status + "] - " + str(len(self._ballot_box)) + " ballots in box"


# if __name__ == "__main__":
#     from crypto.rsa_core import generate_rsa_keypair
#     from crypto.rsa_ops import rsa_encrypt, rsa_sign
#     from crypto.blind_signature import blind_message, unblind_signature

#     decomp = Decompteur()
#     pub_d = decomp.setup_keys(bits=512)
#     e_D = pub_d["e_D"]
#     N_D = pub_d["N_D"]

#     # Simulate the administrator
#     e_A, d_A, N_A = generate_rsa_keypair(bits=512)
#     decomp.set_admin_pubkey(e_A, N_A)

#     print("\nSimulating 3 voters casting votes")
#     votes = [7, 9, 7]

#     for idx, vote_val in enumerate(votes):
#         # Simulate encode_vote output from M5
#         encoded = vote_val % N_A

#         # Voter blinds, admin signs blind, voter unblinds
#         m_masked, k = blind_message(encoded, e_A, N_A)
#         s_blind = pow(m_masked, d_A, N_A)
#         signature = (s_blind * pow(k, -1, N_A)) % N_A

#         # Voter encrypts ballot with decompteur public key and sends to anonymiser
#         encrypted_vote = rsa_encrypt(encoded, e_D, N_D)

#         # Anonymiser forwards to decompteur
#         decomp.receive_vote(encrypted_vote, signature)
#         print("Voter", idx + 1, "voted:", vote_val)

#     results = decomp.decrypt_and_count()
#     print("\nFinal results:", decomp.return_results())

#     assert results[7] == 2
#     assert results[9] == 1
#     print("\nAll tests passed")