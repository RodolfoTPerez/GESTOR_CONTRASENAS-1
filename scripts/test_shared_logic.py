import sqlite3
import hashlib
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Config
DB_PATH = "data/vault_rodolfo.db"
VAULT_ID = "a8e77bff-27da-4bfe-84bf-1efafc07ec71"

def rescue_with_shared_logic():
    print(f"--- Forensic Rescue: Shared Key Logic ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Analyze only DANIEL's records that are likely locked
    secrets = cursor.execute("SELECT id, service, secret, nonce FROM secrets WHERE owner_name LIKE '%DANI%'").fetchall()
    
    # Possible Shared IDs
    # Adding more candidates observed in codebase or derived from environment
    ids = [None, "None", "null", "", "0", "1", "2", "3", "4", "5", "default", "KAREN", "admin", "DANIEL", "RODOLFO", VAULT_ID, VAULT_ID[:8]]
    
    # Pre-derive all possible keys to be fast
    keys = []
    for pid in ids:
        shared_secret = f"PASSGUARDIAN_VAULT_{pid}_SHARED_KEY"
        # Standard PBKDF2 iterations=100k, salt 'public_salt'
        k = hashlib.pbkdf2_hmac('sha256', shared_secret.encode(), b'public_salt', 100000, 32)
        keys.append((k, f"Iter100k_{pid}"))
        
        # Also try raw SHA256 of the secret
        ks = hashlib.sha256(shared_secret.encode()).digest()
        keys.append((ks, f"RawSHA256_{pid}"))

    recovered = 0
    for s in secrets:
        enc_data = bytes(s['secret'])
        nonce = bytes(s['nonce'])
        
        for k, label in keys:
            try:
                decrypted = AESGCM(k).decrypt(nonce, enc_data, None)
                print(f"✅ RECOVERED [{s['service']}] with key: {label}")
                recovered += 1
                # If we recovered it, we can re-encrypt it with the new key here,
                # but let's first see if we found the key.
                break
            except:
                continue

    print(f"\nRecovery analysis finished. Found {recovered} keys.")
    conn.close()

if __name__ == "__main__":
    rescue_with_shared_logic()
