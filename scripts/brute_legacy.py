import sqlite3
import os
import base64
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Config
USERNAME = "RODOLFO"
PASSWORD = "RODOLFO1111111111"
VAULT_ID = "a8e77bff-27da-4bfe-84bf-1efafc07ec71"
DB_PATH = Path("data") / "vault_rodolfo.db"

def ultimate_brute_force():
    print("--- Ultimate Legacy Key Brute-Force ---")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT wrapped_vault_key, vault_salt, salt FROM users WHERE username='RODOLFO'").fetchone()
    wrapped = user['wrapped_vault_key']
    v_salt = user['vault_salt']
    u_salt = user['salt']
    
    passwords = [PASSWORD, VAULT_ID, "Vultrax", "PassGuardian", "12345678", "password"]
    salts = [v_salt, u_salt, b"", VAULT_ID.encode(), b"salt"]
    iters = [100000, 1000, 10000]
    
    print(f"Testing {len(passwords)} passwords, {len(salts)} salts, {len(iters)} iters...")
    
    for p in passwords:
        for s in salts:
            if s is None: continue
            for it in iters:
                try:
                    kdf = PBKDF2HMAC(hashes.SHA256(), 32, s, it, default_backend())
                    kek = kdf.derive(p.encode('utf-8'))
                    AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                    print(f"FOUND! Pwd={p}, Salt={s!r}, Iters={it}")
                    return
                except: continue
                
    print("Zero results. Shifting to unencrypted theory...")
    # Maybe it's not wrapped? (Unlikely for 60 bytes)
    
    print("Testing RAW SHA256 KEK...")
    import hashlib
    for p in passwords:
        for s in salts:
            if s is None: continue
            try:
                kek = hashlib.sha256(p.encode() + s).digest()
                AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                print(f"FOUND RAW! Pwd={p}, Salt={s!r}")
                return
            except: continue

    print("Failed to recover key.")
    conn.close()

if __name__ == "__main__":
    ultimate_brute_force()
