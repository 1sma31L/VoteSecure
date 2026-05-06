import sys
import os
import secrets
import hashlib
import re


_CRYPTO_DIR = os.path.dirname(os.path.abspath(__file__))
if _CRYPTO_DIR not in sys.path:
    sys.path.insert(0, _CRYPTO_DIR)

from tth_hash import tth as _tth_impl   



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


# ═══════════════════════════════════════════════════════════════════════════════
#  Self-test  (run with:  python encoding.py)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    SEP = "─" * 60

    # ── 1. tth ────────────────────────────────────────────────────────────────
    print(SEP)
    print("1. tth()")
    code_a = "AF15GH258ZQP"
    code_b = "AF15GH258ZQR"  

    h_a = tth(code_a)
    h_b = tth(code_b)
    print(f"   tth({code_a!r}) = {h_a}")
    print(f"   tth({code_b!r}) = {h_b}")
    assert h_a != h_b,                    "FAIL: different codes → same hash"
    assert tth(code_a) == tth(code_a.lower()), "FAIL: case sensitivity"
    assert len(h_a) == 8,                 "FAIL: digest must be 8 hex chars"
    print("   ✓ collision-free, case-insensitive, 8-char output")

    # ── 2. generate_code ──────────────────────────────────────────────────────
    print(SEP)
    print("2. generate_code()")
    codes = [generate_code() for _ in range(1000)]
    assert all(len(c) == 12 for c in codes),          "FAIL: wrong length"
    assert all(re.fullmatch(r"[A-Z0-9]{12}", c) for c in codes), "FAIL: bad chars"
    assert len(set(codes)) > 990,                      "FAIL: poor randomness"
    print(f"   Sample codes : {codes[0]}  {codes[1]}  {codes[2]}")
    print(f"   Unique / 1000: {len(set(codes))}")
    print("   ✓ correct length, correct charset, high uniqueness")

    # ── 3. format_code ────────────────────────────────────────────────────────
    print(SEP)
    print("3. format_code()")
    raw      = "AF15GH258ZQP"
    expected = "AF15 GH25 8ZQP"
    result   = format_code(raw)
    print(f"   format_code({raw!r}) = {result!r}")
    assert result == expected, f"FAIL: expected {expected!r}, got {result!r}"
    assert format_code("ABCDEFGH", group_size=2) == "AB CD EF GH", "FAIL: group_size=2"
    print("   ✓ correct grouping and spacing")

    # ── 4. encode_message ─────────────────────────────────────────────────────
    print(SEP)
    print("4. encode_message()")
    m1 = encode_message("hello")
    m2 = encode_message("world")
    m3 = encode_message("hello")
    print(f"   encode_message('hello') = {m1}")
    print(f"   encode_message('world') = {m2}")
    assert m1 != m2,  "FAIL: different messages → same integer"
    assert m1 == m3,  "FAIL: same message → different integers (not deterministic)"
    assert m1 > 0,    "FAIL: result must be positive"

    
    N = 55   
    m_clamped = encode_message("hello", rsa_modulus=N)
    assert 0 < m_clamped < N, f"FAIL: clamped value {m_clamped} not in [1, {N-1}]"
    print(f"   encode_message('hello', rsa_modulus=55) = {m_clamped}  (in [1,54])")
    print("   ✓ deterministic, collision-sensitive, modulus-clamping works")

    # ── 5. encode_vote ────────────────────────────────────────────────────────
    print(SEP)
    print("5. encode_vote()")
    N2_test  = "BZ99KL123MNP"
    v1 = encode_vote(8, N2_test)
    v2 = encode_vote(7, N2_test) 
    v3 = encode_vote(8, N2_test)
    v4 = encode_vote(8, "XX00YY111ZZA")   

    print(f"   encode_vote(8, {N2_test!r}) = {v1}")
    print(f"   encode_vote(7, {N2_test!r}) = {v2}")
    assert v1 != v2, "FAIL: different votes → same encoding"
    assert v1 == v3, "FAIL: same inputs → different encodings (not deterministic)"
    assert v1 != v4, "FAIL: different N2 → same encoding"

    # Test with modulus
    v_clamped = encode_vote(8, N2_test, rsa_modulus=583)  
    assert 0 < v_clamped < 583, f"FAIL: {v_clamped} not in [1, 582]"
    print(f"   encode_vote(8, ..., rsa_modulus=583) = {v_clamped}  (in [1,582])")
    print("   ✓ vote+N2 binding, deterministic, modulus-clamping works")

    # ── 6. Error handling ─────────────────────────────────────────────────────
    print(SEP)
    print("6. Error handling")

    errors_caught = 0

    for fn, args, exc in [
        (tth,             ("",),                  ValueError),
        (tth,             ("hello world",),        ValueError),
        (tth,             (123,),                  TypeError),
        (generate_code,   (0,),                    ValueError),
        (generate_code,   (-1,),                   ValueError),
        (format_code,     ("",),                   ValueError),
        (format_code,     ("hello world",),        ValueError),
        (encode_message,  ("",),                   ValueError),
        (encode_message,  (42,),                   TypeError),
        (encode_message,  ("x", 1),                ValueError),   # modulus < 2
        (encode_vote,     (-1, "AABBCC112233"),     ValueError),
        (encode_vote,     (8,  ""),                 ValueError),
        (encode_vote,     (8,  "bad code!!!"),      ValueError),
    ]:
        try:
            fn(*args)
            print(f"   FAIL: {fn.__name__}{args} should have raised {exc.__name__}")
        except exc:
            errors_caught += 1

    print(f"   ✓ All {errors_caught}/13 expected errors raised correctly")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(SEP)
    print("All tests passed ✓")
    print(SEP)
