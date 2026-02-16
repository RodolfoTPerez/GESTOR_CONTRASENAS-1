import sqlite3
from pathlib import Path
import hashlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# User Config
USERNAME = "RODOLFO"
PASSWORD = "RODOLFO1111111111"
DB_PATH = Path("data") / f"vault_{USERNAME.lower()}.db"

def verify_hash():
    print(f"--- Verifying password hash for {USERNAME} ---")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    user = cursor.execute("SELECT password_hash, salt FROM users WHERE username=?", (USERNAME.upper(),)).fetchone()
    if not user:
        print("User not found.")
        return

    stored_hash = user['password_hash']
    salt = user['salt']
    
    if isinstance(salt, str):
        try: salt = bytes.fromhex(salt)
        except: salt = salt.encode()

    print(f"Stored Hash: {stored_hash}")
    
    # Calculate hash using CryptoEngine standard (100k iters)
    kdf = PBKDF2HMAC(hashes.SHA256(), 32, salt, 100000, default_backend())
    calculated_hash = kdf.derive(PASSWORD.encode('utf-8')).hex()
    
    print(f"Calculated Hash: {calculated_hash}")
    
    if calculated_hash == stored_hash:
        print("✅ PASSWORD MATCHES!")
    else:
        print("❌ PASSWORD MISMATCH!")
        
    conn.close()

if __name__ == "__main__":
    verify_hash()
