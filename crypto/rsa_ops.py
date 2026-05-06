def rsa_encrypt(m: int, e: int, N: int) -> int:
    # RSA encryption:  c = m^e mod N
    if not (0 <= m < N):
        raise ValueError(f"Message m={m} out of range [0, N).")
    return pow(m, e, N)


def rsa_decrypt(c: int, d: int, N: int) -> int:
    # RSA decryption:  m = c^d mod N
    if not (0 <= c < N):
        raise ValueError(f"Ciphertext c={c} out of range [0, N).")
    return pow(c, d, N)


def rsa_sign(m: int, d: int, N: int) -> int:
    # RSA signing:  s = m^d mod N
    if not (0 <= m < N):
        raise ValueError(f"Message m={m} out of range [0, N).")
    return pow(m, d, N)


def rsa_verify(m: int, s: int, e: int, N: int) -> bool:
    # RSA verification:  checks s^e ≡ m (mod N)
    return pow(s, e, N) == m



# if __name__ == "__main__":  
#     # for testing 
#     N = 3233  
#     e = 17    # public exponent
#     d = 2753  # private exponent

#     message = 1234
#     print(f"Original message: {message}")

#     # Encrypt the message
#     ciphertext = rsa_encrypt(message, e, N)
#     print(f"Encrypted message: {ciphertext}")

#     # Decrypt the message
#     decrypted_message = rsa_decrypt(ciphertext, d, N)
#     print(f"Decrypted message: {decrypted_message}")

#     # Sign the message
#     signature = rsa_sign(message, d, N)
#     print(f"Signature: {signature}")

#     # Verify the signature
#     is_valid = rsa_verify(message, signature, e, N)
#     print(f"Signature valid: {is_valid}")