import sqlite3
import os
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# User Config
DB_PATH = "data/vault_rodolfo.db"
PASSWORD = "RODOLFO1111111111"

def test_200k_iterations():
    print(f"--- Forensic Test: 200k Iterations ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT wrapped_vault_key, vault_salt, salt FROM users WHERE username='RODOLFO'").fetchone()
    wrapped = user['wrapped_vault_key']
    v_salt = user['vault_salt']
    u_salt = user['salt']
    
    # Get meta_salt if exists
    meta_salt = None
    try:
        m = conn.execute("SELECT value FROM meta WHERE key='master_salt'").fetchone()
        if m: meta_salt = bytes(m['value'])
    except: pass

    ids = ["RODOLFO1111111111", "RODOLFO"]
    salts = [v_salt, u_salt, meta_salt]
    iters = [100000, 200000, 600000]
    
    for p in ids:
        for s in salts:
            if s is None: continue
            for it in iters:
                try:
                    kdf = PBKDF2HMAC(hashes.SHA256(), 32, s, it, default_backend())
                    kek = kdf.derive(p.encode('utf-8'))
                    dec = AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                    print(f"✅ SUCCESS! Unwrapped with PW='{p}', Salt={s.hex()[:6]}, Iters={it}")
                    return
                except: continue

    print("Failed with 200k and variations.")
    conn.close()

if __name__ == "__main__":
    test_200k_iterations()
