import os
import sqlite3
import hashlib
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

def ultra_recovery_simulation():
    print("--- Ultra Recovery Simulation (V5.1) ---")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT wrapped_vault_key, vault_salt, salt FROM users WHERE username='RODOLFO'").fetchone()
    wrapped = user['wrapped_vault_key']
    current_salt = user['vault_salt']
    
    # EXACTLY the candidates from secrets_manager.py
    salt_candidates = [
        current_salt,
        b"public_salt", 
        b"", 
        b"salt_123",
        USERNAME.upper().encode(),
        USERNAME.lower().encode(),
        USERNAME.encode(),
        user['salt'], # profile.get("salt")
        VAULT_ID.encode()
    ]
    
    iters = [100000, 600000]
    passwords = [PASSWORD, PASSWORD.strip()]
    
    found = False
    
    print(f"Level 1: PBKDF2 Trials...")
    for p in passwords:
        for s in salt_candidates:
            if s is None: continue
            if isinstance(s, str): s = s.encode()
            for it in iters:
                try:
                    kdf = PBKDF2HMAC(hashes.SHA256(), 32, s, it, default_backend())
                    kek = kdf.derive(p.encode('utf-8'))
                    dec = AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                    print(f"✅ SUCCESS LEVEL 1! Salt={s!r}, It={it}, Pwd='{p}'")
                    found = True; break
                except: continue
            if found: break
        if found: break

    if not found:
        print("Level 2: Legacy Raw Hashes...")
        for p in passwords:
            for s in salt_candidates:
                if s is None: continue
                if isinstance(s, str): s = s.encode()
                try:
                    # Raw
                    kek = hashlib.sha256(p.encode('utf-8') + s).digest()
                    dec = AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                    print(f"✅ SUCCESS LEVEL 2 (Raw)! Salt={s!r}, Pwd='{p}'")
                    found = True; break
                except: pass
                
                try:
                    # Hex
                    s_hex = s.hex() if isinstance(s, bytes) else s
                    kek = hashlib.sha256((p + s_hex).encode('utf-8')).digest()
                    dec = AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                    print(f"✅ SUCCESS LEVEL 2 (Hex)! Salt={s!r}, Pwd='{p}'")
                    found = True; break
                except: pass
            if found: break

    if found:
        print("Legacy key recovered! Now we can translate the records.")
    else:
        print("FAILED Ultra Recovery.")
    
    conn.close()

if __name__ == "__main__":
    ultra_recovery_simulation()
