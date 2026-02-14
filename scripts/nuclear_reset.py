
import sys
import os
import sqlite3
import secrets
import argparse
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_kek(password: str, salt: bytes, iterations: int = 100000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))

def wrap_key(key: bytes, password: str, salt: bytes) -> bytes:
    kek = derive_kek(password, salt)
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(kek).encrypt(nonce, key, None)

def main():
    parser = argparse.ArgumentParser(description="Nuclear Vault Reset for PassGuardian")
    parser.add_argument("--password", required=True, help="Current login password")
    parser.add_argument("--username", default="RODOLFO", help="Username to reset (default: RODOLFO)")
    args = parser.parse_args()

    username = args.username.upper()
    password = args.password
    db_path = Path(f"data/vault_{username.lower()}.db")

    print(f"[*] Starting Nuclear Reset for {username}...")
    
    if not db_path.exists():
        print(f"[-] Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        print(f"[-] Error: User {username} not found in DB.")
        return

    v_salt = bytes(user['vault_salt']) if user['vault_salt'] else secrets.token_bytes(16)
    v_id = user['vault_id']
    
    print(f"[*] Generating NEW Vault Master Key...")
    new_key = secrets.token_bytes(32)
    wrapped_key = wrap_key(new_key, password, v_salt)

    try:
        # Update users table
        cursor.execute("UPDATE users SET wrapped_vault_key=?, vault_salt=? WHERE username=?", 
                       (sqlite3.Binary(wrapped_key), sqlite3.Binary(v_salt), username))
        
        # Ensure vault_access exists (without user_id column)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vault_access'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE vault_access (
                    vault_id TEXT PRIMARY KEY,
                    wrapped_master_key BLOB,
                    access_level TEXT DEFAULT 'member',
                    updated_at INTEGER,
                    synced INTEGER DEFAULT 1
                )
            """)

        # Update vault_access
        cursor.execute("""
            INSERT OR REPLACE INTO vault_access 
            (vault_id, wrapped_master_key, access_level, updated_at, synced) 
            VALUES (?, ?, ?, ?, 1)
        """, (v_id, sqlite3.Binary(wrapped_key), 'admin', int(time.time())))
        
        conn.commit()
        print(f"[+] SUCCESS: Vault has been reset successfully.")
        print(f"[!] Warning: Previous encrypted secrets in this vault are now lost.")
    except Exception as e:
        print(f"[-] Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
