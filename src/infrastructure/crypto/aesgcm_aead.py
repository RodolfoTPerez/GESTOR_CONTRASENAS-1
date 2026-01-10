import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt(plaintext: str, key: bytes) -> tuple[bytes, bytes]:
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode(), None)
    return ct, nonce

def decrypt(ciphertext: bytes, key: bytes, nonce: bytes) -> str:
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None).decode()