import sqlite3
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# User Config
PASSWORD = "RODOLFO1111111111"
TEST_SALT = bytes.fromhex("a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
DB_PATH = "data/vault_rodolfo.db"

def test_config_salt():
    print(f"--- Forensic Test: Config Salt '{TEST_SALT.hex()}' ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT wrapped_vault_key FROM users WHERE username='RODOLFO'").fetchone()
    wrapped = user['wrapped_vault_key']
    
    iters = [100000, 1000, 600000]
    
    for it in iters:
        try:
            kdf = PBKDF2HMAC(hashes.SHA256(), 32, TEST_SALT, it, default_backend())
            kek = kdf.derive(PASSWORD.encode('utf-8'))
            dec = AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
            print(f"✅ SUCCESS! Unwrapped with Config Salt, Iters={it}")
            return
        except: continue
    print("Failed with this salt.")
    conn.close()

if __name__ == "__main__":
    test_config_salt()
