import os
import sqlite3
import base64
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# User Config
USERNAME = "RODOLFO"
PASSWORD = "RODOLFO1111111111"
DB_PATH = Path("data") / f"vault_{USERNAME.lower()}.db"

def translate_keys():
    print("--- Local Key Translation: Internal Repair ---")
    
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch BOTH keys from the local DB
    # We found that 'users' has the OLD and 'vault_access' has the NEW
    user_row = cursor.execute("SELECT wrapped_vault_key, vault_salt FROM users WHERE username=?", (USERNAME.upper(),)).fetchone()
    access_row = cursor.execute("SELECT wrapped_master_key FROM vault_access WHERE vault_id=?", ("a8e77bff-27da-4bfe-84bf-1efafc07ec71",)).fetchone()

    if not user_row or not access_row:
        print("Missing key rows.")
        return

    old_wrapped = user_row['wrapped_vault_key']
    new_wrapped = access_row['wrapped_master_key']
    salt = user_row['vault_salt']

    print(f"Old Key Hash: {old_wrapped.hex()[:10]}...")
    print(f"New Key Hash: {new_wrapped.hex()[:10]}...")

    # 2. Derive VMKs
    def unwrap(wrapped, s, p):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=s, iterations=100000, backend=default_backend())
        kek = kdf.derive(p.encode('utf-8'))
        return AESGCM(kek).decrypt(wrapped[:12], wrapped[12:], None)

    try:
        old_vmk = unwrap(old_wrapped, salt, PASSWORD)
        print("✅ Successfully unwrapped OLD VMK from users table.")
    except Exception as e:
        print(f"❌ Failed to unwrap OLD VMK: {e}")
        return

    try:
        new_vmk = unwrap(new_wrapped, salt, PASSWORD)
        print("✅ Successfully unwrapped NEW VMK from vault_access table.")
    except Exception as e:
        print(f"❌ Failed to unwrap NEW VMK: {e}")
        return

    # 3. Translate Secrets
    secrets = cursor.execute("SELECT id, service, secret, nonce FROM secrets WHERE vault_id=?", ("a8e77bff-27da-4bfe-84bf-1efafc07ec71",)).fetchall()
    migrated = 0
    
    for s in secrets:
        # Try new key - skip if already working
        try:
            AESGCM(new_vmk).decrypt(s['nonce'], s['secret'], None)
            continue
        except:
            # Try old key
            try:
                plaintext = AESGCM(old_vmk).decrypt(s['nonce'], s['secret'], None)
                # Success! Translate
                new_nonce = os.urandom(12)
                new_secret = AESGCM(new_vmk).encrypt(new_nonce, plaintext, None)
                
                cursor.execute("UPDATE secrets SET secret=?, nonce=?, synced=0 WHERE id=?", 
                               (sqlite3.Binary(new_secret), sqlite3.Binary(new_nonce), s['id']))
                migrated += 1
                print(f"Translated: {s['service']}")
            except:
                pass

    # 4. Final step: Sync the users table with the NEW key to be consistent
    print("Updating users table to match the new VMK...")
    cursor.execute("UPDATE users SET wrapped_vault_key = ? WHERE username = ?", (sqlite3.Binary(new_wrapped), USERNAME.upper()))

    conn.commit()
    conn.close()
    
    print(f"\nMigration complete. {migrated} records restored.")

if __name__ == "__main__":
    translate_keys()
