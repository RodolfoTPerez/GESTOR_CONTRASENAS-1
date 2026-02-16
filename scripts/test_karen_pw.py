import sqlite3
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Config
DB_PATH = "data/vault_rodolfo.db"
PASSWORD_CANDIDATE = "KAREN"

def test_karen_password():
    print(f"--- Forensic Test: Password '{PASSWORD_CANDIDATE}' ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT wrapped_vault_key, vault_salt, salt FROM users WHERE username='KAREN'").fetchone()
    if not user:
        # Try from RODOLFO'S entry if KAREN doesn't exist in users table (only in vault_access)
        user = conn.execute("SELECT wrapped_vault_key, vault_salt, salt FROM users WHERE username='RODOLFO'").fetchone()

    wrapped = user['wrapped_vault_key']
    v_salt = user['vault_salt']
    u_salt = user['salt']
    
    salts = [v_salt, u_salt, b""]
    iters = [100000, 1000]
    
    for s in salts:
        if s is None: continue
        for it in iters:
            try:
                kdf = PBKDF2HMAC(hashes.SHA256(), 32, s, it, default_backend())
                kek = kdf.derive(PASSWORD_CANDIDATE.encode('utf-8'))
                dec = AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                print(f"✅ SUCCESS! Unwrapped with password '{PASSWORD_CANDIDATE}', Salt={s.hex()[:6]}, Iters={it}")
                print(f"Recovered VMK: {dec.hex()}")
                return
            except: continue
    print("Failed with this password.")
    conn.close()

if __name__ == "__main__":
    test_karen_password()
