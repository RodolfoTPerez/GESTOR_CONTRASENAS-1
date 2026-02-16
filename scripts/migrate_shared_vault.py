import sys
import os
import sqlite3
import base64
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.remote_storage_client import RemoteStorageClient
from config.config import SUPABASE_URL, SUPABASE_KEY
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# User Config
USERNAME = "RODOLFO"
PASSWORD = "RODOLFO1111111111"
DB_PATH = Path("data") / f"vault_{USERNAME.lower()}.db"

def migrate():
    print("--- Shared Record Migration: Key Translation ---")
    
    # 1. Connect to Cloud to get OLD key
    client = RemoteStorageClient(SUPABASE_URL, SUPABASE_KEY)
    
    # Get user ID
    res = client.get_records("users", f"select=id,vault_salt&username=ilike.{USERNAME}")
    if not res:
        print("User not found in cloud.")
        return
    user_id = res[0]['id']
    cloud_vault_salt = res[0]['vault_salt']
    
    if isinstance(cloud_vault_salt, str) and cloud_vault_salt.startswith('\\x'):
        cloud_vault_salt = bytes.fromhex(cloud_vault_salt[2:])
    elif isinstance(cloud_vault_salt, str):
        cloud_vault_salt = base64.b64decode(cloud_vault_salt)

    # Get OLD wrapped key from vault_access
    access = client.get_records("vault_access", f"select=*&user_id=eq.{user_id}")
    if not access:
        print("No vault access found in cloud.")
        return
    
    old_wrapped_key = access[0]['wrapped_master_key']
    if isinstance(old_wrapped_key, str):
        old_wrapped_key = bytes.fromhex(old_wrapped_key)
        
    print(f"Old wrapped key fetched: {len(old_wrapped_key)} bytes")

    # 2. Derive OLD VMK
    kdf_old = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=cloud_vault_salt,
        iterations=100000,
        backend=default_backend()
    )
    kek_old = kdf_old.derive(PASSWORD.encode('utf-8'))
    old_vmk = AESGCM(kek_old).decrypt(old_wrapped_key[:12], old_wrapped_key[12:], None)
    print("Successfully unwrapped OLD VMK.")

    # 3. Connect to Local DB to get NEW VMK
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    local_user = cursor.execute("SELECT wrapped_vault_key, vault_salt FROM users WHERE username=?", (USERNAME.upper(),)).fetchone()
    new_wrapped_key = local_user['wrapped_vault_key']
    new_vault_salt = local_user['vault_salt']
    
    # Derive NEW VMK
    kdf_new = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=new_vault_salt,
        iterations=100000,
        backend=default_backend()
    )
    kek_new = kdf_new.derive(PASSWORD.encode('utf-8'))
    new_vmk = AESGCM(kek_new).decrypt(new_wrapped_key[:12], new_wrapped_key[12:], None)
    print("Successfully unwrapped NEW VMK.")

    # 4. Migrate Records
    secrets = cursor.execute("SELECT id, service, secret, nonce, vault_id FROM secrets WHERE vault_id=?", (access[0]['vault_id'],)).fetchall()
    migrated_count = 0
    failed_count = 0
    
    print(f"Analyzing {len(secrets)} secrets for vault {access[0]['vault_id']}...")
    
    for s in secrets:
        # Try to decrypt with NEW key first
        try:
            AESGCM(new_vmk).decrypt(s['nonce'], s['secret'], None)
            # If succeeds, already migrated
            continue
        except Exception:
            # Try decrypt with OLD key
            try:
                decrypted = AESGCM(old_vmk).decrypt(s['nonce'], s['secret'], None)
                # Success! Re-encrypt with NEW key
                new_nonce = os.urandom(12)
                new_secret = AESGCM(new_vmk).encrypt(new_nonce, decrypted, None)
                
                cursor.execute("UPDATE secrets SET secret=?, nonce=?, synced=0 WHERE id=?", 
                               (sqlite3.Binary(new_secret), sqlite3.Binary(new_nonce), s['id']))
                migrated_count += 1
                print(f"Migrated record: {s['service']}")
            except Exception as e:
                failed_count += 1
                # print(f"Failed record {s['service']}: {e}")

    conn.commit()
    conn.close()
    
    print(f"\nMigration complete.")
    print(f"Total migrated: {migrated_count}")
    print(f"Failed/Skipped: {failed_count}")
    print("Now RODOLFO can see everything unlocked.")

if __name__ == "__main__":
    migrate()
