import secrets
import math


def blind_message(m: int, e: int, N: int) -> tuple[int, int]:
    if not (0 < m < N):
        raise ValueError(f"m must satisfy 0 < m < N. Got m={m}.")

    # Cryptographically secure blinding factor
    while True:
        k = secrets.randbelow(N)
        if k > 1 and math.gcd(k, N) == 1:
            break

    r = pow(k, e, N)
    m_masked = (m * r) % N
    return m_masked, k


def sign_blind(m_masked: int, d: int, N: int) -> int:
    if not (0 <= m_masked < N):
        raise ValueError(f"m_masked must be in [0, N).")
    return pow(m_masked, d, N)


def unblind_signature(s_blind: int, k: int, N: int) -> int:
    if math.gcd(k, N) != 1:
        raise ValueError("k must be coprime with N.")
    k_inv = pow(k, -1, N)
    return (s_blind * k_inv) % N

if __name__ == "__main__":
    # Example usage
    N = 3233
    e = 17
    d = 2753

    message = 1234
    print(f"Original message: {message}")

    m_masked, k = blind_message(message, e, N)
    print(f"Blinded message: {m_masked}, Blinding factor k: {k}")

    s_blind = sign_blind(m_masked, d, N)
    print(f"Blind signature: {s_blind}")

    signature = unblind_signature(s_blind, k, N)
    print(f"Unblinded signature: {signature}")