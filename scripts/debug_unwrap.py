import sqlite3
from pathlib import Path
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# User Config
USERNAME = "RODOLFO"
PASSWORD = "RODOLFO1111111111"
DB_PATH = Path("data") / f"vault_{USERNAME.lower()}.db"

def debug_unwrap():
    print("--- Forensic Debug: Unwrapping Legacy Key ---")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    user = cursor.execute("SELECT * FROM users WHERE username=?", (USERNAME.upper(),)).fetchone()
    if not user: return
    
    wrapped = user['wrapped_vault_key']
    salts = {
        "vault_salt": user['vault_salt'],
        "user_salt": user['salt']
    }
    
    if isinstance(salts['user_salt'], str):
        try: salts['user_salt'] = bytes.fromhex(salts['user_salt'])
        except: salts['user_salt'] = salts['user_salt'].encode()

    iters = [100000, 600000, 50000, 10000, 1000]
    
    print(f"Testing {len(salts)} salts and {len(iters)} iters on key {wrapped.hex()[:10]}...")
    
    for salt_name, s in salts.items():
        if not s: continue
        for it in iters:
            try:
                kdf = PBKDF2HMAC(hashes.SHA256(), 32, s, it, default_backend())
                kek = kdf.derive(PASSWORD.encode('utf-8'))
                AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)
                print(f"SUCCESS! Found match: Salt={salt_name} ({s.hex()[:8]}), Iters={it}")
                return
            except: continue
            
    print("No match found with standard PBKDF2.")
    conn.close()

if __name__ == "__main__":
    debug_unwrap()
