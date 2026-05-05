import random

def is_prime(n, rounds=20):
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits=1024):
    while True:
        candidate = random.getrandbits(bits)
        candidate |= (1 << bits - 1) | 1
        if is_prime(candidate):
            return candidate


def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    gcd, x1, y1 = extended_gcd(b, a % b)
    return gcd, y1, x1 - (a // b) * y1


def mod_inverse(a, m):
    gcd, x, _ = extended_gcd(a % m, m)
    if gcd != 1:
        raise ValueError(f"No modular inverse exists for {a} mod {m}")
    return x % m


def generate_rsa_keypair(bits=2048):
    e = 65537
    while True:
        p = generate_prime(bits // 2)
        q = generate_prime(bits // 2)
        if p == q:
            continue
        N = p * q
        phi = (p - 1) * (q - 1)
        gcd, _, _ = extended_gcd(e, phi)
        if gcd != 1:
            continue
        d = mod_inverse(e, phi)
        return e, d, N
