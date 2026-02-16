import sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PASSWORD = "RODOLFO1111111111"
DB_PATH = Path("data") / "vault_rodolfo.db"

def test_no_salt():
    print("--- Forensic Test: Salt-less Unwrap ---")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT wrapped_vault_key FROM users WHERE username='RODOLFO'").fetchone()
    wrapped = user['wrapped_vault_key']
    
    # Try with NO salt (empty bytes) or some constant
    salts = [b"", b"\x00"*16, b"salt", USERNAME.upper().encode()]
    iters = [100000, 1000]
    
    for s in salts:
        for it in iters:
            try:
                kdf = PBKDF2HMAC(hashes.SHA256(), 32, s, it, default_backend())
                kek = kdf.derive(PASSWORD.encode('utf-8'))
                AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                print(f"SUCCESS! Salt-less unwrap worked with salt={s!r} and iters={it}")
                return
            except: continue
    print("Failed salt-less unwrap.")
    conn.close()

if __name__ == "__main__":
    test_no_salt()
