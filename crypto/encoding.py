import sys
import os
import secrets
import hashlib
import re


_CRYPTO_DIR = os.path.dirname(os.path.abspath(__file__))
if _CRYPTO_DIR not in sys.path:
    sys.path.insert(0, _CRYPTO_DIR)

from hash import tth as _tth_impl   
from hash import hash_n2, secure_hash



_CODE_ALPHABET: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_DEFAULT_CODE_LENGTH: int = 12

_FORMAT_GROUP_SIZE: int = 4


_SHORT_DIGEST_BYTES: int = 4 


# ═══════════════════════════════════════════════════════════════════════════════
#  1. TTH Hash  (thin wrapper  keeps a single import point for the rest of the
#               project; all callers import from encoding, not tth_hash directly)
# ═══════════════════════════════════════════════════════════════════════════════

def tth(text: str) -> str:
   
    if not isinstance(text, str):
        raise TypeError(f"tth() expects a str, got {type(text).__name__!r}.")
    if not text:
        raise ValueError("tth() received an empty string.")
    if not re.fullmatch(r"[A-Za-z0-9]+", text):
        raise ValueError(
            f"tth() only accepts alphanumeric characters. "
            f"Got: {text!r}"
        )
    return _tth_impl(text)


# ═══════════════════════════════════════════════════════════════════════════════
#  2. Secure Code Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_code(length: int = _DEFAULT_CODE_LENGTH) -> str:
   
    if not isinstance(length, int):
        raise TypeError(f"length must be an int, got {type(length).__name__!r}.")
    if length < 1:
        raise ValueError(f"length must be ≥ 1, got {length}.")

    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


# ═══════════════════════════════════════════════════════════════════════════════
#  3. Code Formatting
# ═══════════════════════════════════════════════════════════════════════════════

def format_code(code: str, group_size: int = _FORMAT_GROUP_SIZE) -> str:
 
    if not isinstance(code, str):
        raise TypeError(f"code must be a str, got {type(code).__name__!r}.")
    if not code:
        raise ValueError("code must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9]+", code):
        raise ValueError(
            f"code must contain only alphanumeric characters. Got: {code!r}"
        )
    if not isinstance(group_size, int):
        raise TypeError(
            f"group_size must be an int, got {type(group_size).__name__!r}."
        )
    if group_size < 1:
        raise ValueError(f"group_size must be ≥ 1, got {group_size}.")

    code = code.upper()
    groups = [code[i : i + group_size] for i in range(0, len(code), group_size)]
    return " ".join(groups)


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Message Encoding  (string → RSA-safe integer)
# ═══════════════════════════════════════════════════════════════════════════════

def encode_message(msg: str, rsa_modulus: int = None) -> int:
    if not isinstance(msg, str):
        raise TypeError(f"msg must be a str, got {type(msg).__name__!r}.")
    if not msg:
        raise ValueError("msg must not be empty.")
    if rsa_modulus is not None:
        if not isinstance(rsa_modulus, int):
            raise TypeError(f"rsa_modulus must be an int, got {type(rsa_modulus).__name__!r}.")
        if rsa_modulus < 2:
            raise ValueError(f"rsa_modulus must be ≥ 2, got {rsa_modulus}.")

    # hash
    m_hash = hashlib.sha256(msg.encode("utf-8")).digest()        # 32 bytes

    if rsa_modulus is None:
        return int.from_bytes(m_hash, "big")

    #  MGF1 seed
    mgf_seed = hashlib.sha256(m_hash + b"\x00").digest()         # 32 bytes

    # Data Block  =  hash || mgf_seed || 0xBC
    db = m_hash + mgf_seed + b"\xbc"                             # 65 bytes

    # Step 4 : ajuster à la taille du modulus
    em_len = (rsa_modulus.bit_length() + 7) // 8
    if len(db) < em_len:
        padded = b"\x00" * (em_len - len(db)) + db
    else:
        padded = db[-em_len:]

    # entier dans [1, N-1] sans biais
    padded_int = int.from_bytes(padded, "big")
    result = (padded_int % (rsa_modulus - 1)) + 1

    return result
# ═══════════════════════════════════════════════════════════════════════════════
#  5. Vote Encoding  (vote + N2 → RSA-safe integer)
# ═══════════════════════════════════════════════════════════════════════════════

def encode_vote(vote: int, N2: str, rsa_modulus: int = None) -> int:
   
   
    if not isinstance(vote, int):
        raise TypeError(f"vote must be an int, got {type(vote).__name__!r}.")
    if vote < 0:
        raise ValueError(f"vote must be ≥ 0, got {vote}.")
    if not isinstance(N2, str):
        raise TypeError(f"N2 must be a str, got {type(N2).__name__!r}.")
    if not N2:
        raise ValueError("N2 must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9]+", N2):
        raise ValueError(
            f"N2 must contain only alphanumeric characters. Got: {N2!r}"
        )


    ballot_str = f"{vote}|{N2.upper()}"
    return encode_message(ballot_str, rsa_modulus=rsa_modulus)

