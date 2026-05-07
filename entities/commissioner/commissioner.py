class Commissioner:
    def __init__(self):
        self.valid_n1_codes = set()
        self.valid_n2_hashes = set()

    def register_voter(self, n1: str, n2_hash: str):
        self.valid_n1_codes.add(n1)
        self.valid_n2_hashes.add(n2_hash)
        print(f"[Commissioner] Voter registered. N1: {n1}")

    def validate_n1(self, n1: str) -> bool:
        if n1 in self.valid_n1_codes:
            print(f"[Commissioner] N1 {n1} is valid.")
            return True
        print(f"[Commissioner] N1 {n1} is INVALID.")
        return False

    def consume_n1(self, n1: str) -> bool:
        if n1 in self.valid_n1_codes:
            self.valid_n1_codes.remove(n1)
            print(f"[Commissioner] N1 {n1} consumed (vote recorded).")
            return True
        print(f"[Commissioner] N1 {n1} not found or already used.")
        return False

    def register_n2_hash(self, n2_hash: str):
        self.valid_n2_hashes.add(n2_hash)

    def verify_n2_hash(self, n2_hash: str) -> bool:
        result = n2_hash in self.valid_n2_hashes
        print(f"[Commissioner] N2 hash {'valid' if result else 'INVALID'}.")
        return result
