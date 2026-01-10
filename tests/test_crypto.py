import pytest, os
from src.infrastructure.crypto.argon2_kdf import derive_key, generate_salt
from src.infrastructure.crypto.aesgcm_aead import encrypt, decrypt

def test_roundtrip():
    pt = "super_secret"
    key = derive_key("MyPassword123!", generate_salt())
    ct, nonce = encrypt(pt, key)
    assert decrypt(ct, key, nonce) == pt