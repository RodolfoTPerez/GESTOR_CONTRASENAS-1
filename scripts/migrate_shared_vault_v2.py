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

def forensic_recover_old_key():
    print("--- Forensic Recovery of OLD Vault Key ---")
    
    client = RemoteStorageClient(SUPABASE_URL, SUPABASE_KEY)
    res = client.get_records("users", f"select=id,vault_salt,username,salt&username=ilike.{USERNAME}")
    if not res: return
    
    user_id = res[0]['id']
    cloud_vault_salt_raw = res[0]['vault_salt']
    cloud_user_salt_raw = res[0]['salt']
    
    def normalize_salt(s):
        if not s: return None
        if isinstance(s, bytes): return s
        if s.startswith('\\x'): return bytes.fromhex(s[2:])
        try: return base64.b64decode(s)
        except: return s.encode()

    salts = [
        normalize_salt(cloud_vault_salt_raw),
        normalize_salt(cloud_user_salt_raw),
        USERNAME.upper().encode(),
        USERNAME.encode()
    ]
    
    # Add local salts from vultrax if possible
    try:
         v_conn = sqlite3.connect("data/vultrax.db")
         v_cursor = v_conn.cursor()
         meta_salts = v_cursor.execute("SELECT value FROM meta WHERE key LIKE '%salt%'").fetchall()
         for ms in meta_salts:
             salts.append(ms[0])
         v_conn.close()
    except: pass

    # Get OLD wrapped key from vault_access
    access = client.get_records("vault_access", f"select=*&user_id=eq.{user_id}")
    if not access: return
    old_wrapped_key = bytes.fromhex(access[0]['wrapped_master_key']) if isinstance(access[0]['wrapped_master_key'], str) else access[0]['wrapped_master_key']

    iters = [100000, 600000, 50000, 10000, 1000]
    
    print(f"Brute-forcing OLD key decryption with {len(salts)} salts and {len(iters)} iteration counts...")
    
    for s in salts:
        if not s: continue
        for it in iters:
            try:
                kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=s, iterations=it, backend=default_backend())
                kek = kdf.derive(PASSWORD.encode('utf-8'))
                old_vmk = AESGCM(kek).decrypt(old_wrapped_key[:12], old_wrapped_key[12:], None)
                print(f"SUCCESS! Recovered OLD VMK with salt={s.hex()[:8]} and iters={it}")
                return old_vmk, s, it
            except: continue
            
    # Try legacy SHA256
    import hashlib
    for s in salts:
        if not s: continue
        try:
             raw_key = hashlib.sha256(PASSWORD.encode('utf-8') + s).digest()
             old_vmk = AESGCM(raw_key).decrypt(old_wrapped_key[:12], old_wrapped_key[12:], None)
             print(f"SUCCESS! Recovered OLD VMK with Legacy SHA256 and salt={s.hex()[:8]}")
             return old_vmk, s, "legacy"
        except: continue
        
    print("FAILED to recover OLD VMK.")
    return None, None, None

def migrate_with_recovery():
    old_vmk, old_salt, old_it = forensic_recover_old_key()
    if not old_vmk: return

    # Connect to Local DB to get NEW VMK
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    local_user = cursor.execute("SELECT wrapped_vault_key, vault_salt FROM users WHERE username=?", (USERNAME.upper(),)).fetchone()
    kek_new = PBKDF2HMAC(hashes.SHA256(), 32, local_user['vault_salt'], 100000, default_backend()).derive(PASSWORD.encode('utf-8'))
    new_vmk = AESGCM(kek_new).decrypt(local_user['wrapped_vault_key'][:12], local_user['wrapped_vault_key'][12:], None)

    # Migrate Records
    secrets = cursor.execute("SELECT id, service, secret, nonce FROM secrets").fetchall()
    migrated_count = 0
    
    for s in secrets:
        try:
            # Try NEW key
            AESGCM(new_vmk).decrypt(s['nonce'], s['secret'], None)
            continue
        except:
            try:
                # Try OLD key
                decrypted = AESGCM(old_vmk).decrypt(s['nonce'], s['secret'], None)
                new_nonce = os.urandom(12)
                new_secret = AESGCM(new_vmk).encrypt(new_nonce, decrypted, None)
                cursor.execute("UPDATE secrets SET secret=?, nonce=?, synced=0 WHERE id=?", 
                               (sqlite3.Binary(new_secret), sqlite3.Binary(new_nonce), s['id']))
                migrated_count += 1
                print(f"Migrated: {s['service']}")
            except: continue

    conn.commit()
    conn.close()
    print(f"\nMigration complete. Total migrated: {migrated_count}")

if __name__ == "__main__":
    migrate_with_recovery()
