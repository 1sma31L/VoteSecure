from datetime import datetime
import secrets
import random


class Anonymiser:

    def __init__(self):

        self.seen_signatures = set()

        self.pending_ballots = []

        self.ballot_count = 0

        self.rejected_count = 0

        self.receipts = {}

        self.audit = []

    # ─────────────────────────────────────────────

    def log(self, msg: str):

        self.audit.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "msg": msg
        })

        print(f"[ANONYMISER] {msg}")

    # ─────────────────────────────────────────────

    def signature_already_seen(self, signature: int) -> bool:

        return signature in self.seen_signatures

    # ─────────────────────────────────────────────

    def add_signature(self, signature: int):

        self.seen_signatures.add(signature)

    # ─────────────────────────────────────────────

    def store_ballot(
        self,
        encrypted_ballot: int,
        signature: int,
        m_int: int
    ):

        self.pending_ballots.append({

            "encrypted_ballot": encrypted_ballot,

            "signature": signature,

            "m_int": m_int,

            "timestamp": datetime.now().isoformat()
        })

    # ─────────────────────────────────────────────

    def shuffle_ballots(self):

        random.shuffle(self.pending_ballots)

    # ─────────────────────────────────────────────

    def pop_all_ballots(self):

        ballots = self.pending_ballots.copy()

        self.pending_ballots.clear()

        return ballots

    # ─────────────────────────────────────────────

    def create_receipt(self):

        receipt_id = secrets.token_hex(8)

        self.receipts[receipt_id] = {

            "timestamp": datetime.now().isoformat(),

            "status": "stored"
        }

        return receipt_id

    # ─────────────────────────────────────────────

    def increment_ballot_count(self):

        self.ballot_count += 1

    # ─────────────────────────────────────────────

    def increment_rejected_count(self):

        self.rejected_count += 1

    # ─────────────────────────────────────────────

    def get_receipt(self, receipt_id: str):

        return self.receipts.get(receipt_id)

    # ─────────────────────────────────────────────

    def reset(self):

        self.seen_signatures.clear()

        self.pending_ballots.clear()

        self.ballot_count = 0

        self.rejected_count = 0

        self.receipts.clear()

        self.audit.clear()