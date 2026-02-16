import os
import sqlite3
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PASSWORD = "RODOLFO1111111111"
SALT = bytes.fromhex("cc245e8313b3cad85aca") # From dump_keys

def test_wrap():
    print("--- Test Wrap with Current Parameters ---")
    vmk = b'\x00' * 32 # Dummy key
    
    kdf = PBKDF2HMAC(hashes.SHA256(), 32, SALT, 100000, default_backend())
    kek = kdf.derive(PASSWORD.encode('utf-8'))
    
    nonce = b'\x00' * 12 # Fixed nonce for comparison
    wrapped = nonce + AESGCM(kek).encrypt(nonce, vmk, None)
    
    print(f"Generated Hex (with fixed nonce): {wrapped.hex()}")
    # The first 24 chars are the nonce (all 0), then the ciphertext
    ciphertext_start = wrapped[12:].hex()[:10]
    print(f"Ciphertext starts with: {ciphertext_start}")

if __name__ == "__main__":
    test_wrap()
