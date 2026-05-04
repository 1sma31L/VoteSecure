# tth_hash.py

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
    if remainder != 0:
        padding_needed = block_size - remainder
        values = values + values[:padding_needed]
    return values


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


if __name__ == "__main__":

    # Test 1: basic hash
    code = "GDVESGSDBHSBDDY783374"
    result = tth(code)
    print(f"tth('{code}') = {result}")

    # Test 2: different inputs give different outputs
    code2 = "GDVESGSDBHSBDDY783375"   # last char changed
    r1 = tth(code)
    r2 = tth(code2)
    print(f"tth('{code}')  = {r1}")
    print(f"tth('{code2}')  = {r2}")
    assert r1 != r2, "FAIL: different inputs gave same hash!"
    print("Different hashes confirmed")

    # Test 3: case insensitive
    print("Case insensitive")
    assert tth("GDVESGSDBHSBDDY783374") == tth("gdvesgsdbhsbddy783374"), "FAIL: case sensitivity issue!"
    print("tth('GDVESGSDBHSBDDY783374') == tth('gdvesgsdbhsbddy783374') ✓")
