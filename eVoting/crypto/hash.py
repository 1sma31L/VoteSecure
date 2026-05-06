# tth_hash.py
import hashlib
import re

def _encode_char(c: str) -> int:

    c = c.upper()
    if c.isdigit():
        return int(c)
    elif c.isalpha():
        return ord(c) - ord('A') + 1  
    else:
        raise ValueError(f"Invalid character: '{c}'. Only letters and digits allowed.")


def _encode(text: str) -> list:
    return [_encode_char(c) for c in text]


def _pad(values: list, block_size: int = 16) -> list:
    remainder = len(values) % block_size
    if remainder == 0:
        return values
    padding_needed = block_size - remainder
    repeated = (values * ((padding_needed + len(values) - 1) // len(values)))[:padding_needed]
    return values + repeated


def _mix(block: list) -> list:
    # split block into 4 tetragraphs of 4
    t0 = block[0:4]
    t1 = block[4:8]
    t2 = block[8:12]
    t3 = block[12:16]

    # mix each tetragraph: rotate and XOR with neighbours
    def mix_group(g):
        return [
            (g[0] + g[1]) % 256,
            (g[1] ^ g[2]),
            (g[2] + g[3]) % 256,
            (g[3] ^ g[0]),
        ]

    m0 = mix_group(t0)
    m1 = mix_group(t1)
    m2 = mix_group(t2)
    m3 = mix_group(t3)

    # combine the 4 mixed groups into a single 4-value digest
    return [
        (m0[0] ^ m1[0] ^ m2[0] ^ m3[0]),
        (m0[1] + m1[1] + m2[1] + m3[1]) % 256,
        (m0[2] ^ m1[2] ^ m2[2] ^ m3[2]),
        (m0[3] + m1[3] + m2[3] + m3[3]) % 256,
    ]


def tth(text: str) -> str:

    # Step 1: encode characters to numbers
    values = _encode(text)

    # Step 2: pad to multiple of 16
    values = _pad(values, block_size=16)

    # Step 3: process each block of 16 and accumulate
    digest = [0, 0, 0, 0]
    for i in range(0, len(values), 16):
        block = values[i:i + 16]
        mixed = _mix(block)
        # XOR accumulate into digest
        digest = [digest[j] ^ mixed[j] for j in range(4)]

    # Step 4: return as hex string
    return ''.join(f'{b:02x}' for b in digest)




# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 : secure_hash  (SHA-256 via hashlib)
# ═══════════════════════════════════════════════════════════════════════════════

def secure_hash(text: str) -> str:
    """
    SHA-256 hash  production-grade cryptographic hash function.
    Output : 64 hex characters (256 bits).
    Use for : storing N2 fingerprints
    """
    if not isinstance(text, str):
        raise TypeError(f"secure_hash() expects a str, got {type(text).__name__!r}.")
    if not text:
        raise ValueError("secure_hash() received an empty string.")

    return hashlib.sha256(text.upper().encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 : hash_n2   
#  Calls secure_hash by default, tth if pedagogic=True
# ═══════════════════════════════════════════════════════════════════════════════

def hash_n2(n2: str, pedagogic: bool = False) -> str:
    if not isinstance(n2, str):
        raise TypeError(f"n2 must be a str, got {type(n2).__name__!r}.")
    if not n2:
        raise ValueError("n2 must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9]+", n2):   # ← cette ligne manque
        raise ValueError(f"n2 must be alphanumeric. Got: {n2!r}")
    
    if pedagogic:
        return tth(n2)
    return secure_hash(n2)

