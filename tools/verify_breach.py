
import sqlite3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.infrastructure.secrets_manager import SecretsManager
import os
import hashlib

def verify_privacy_breach():
    sm = SecretsManager()
    # Simulate Rodolfo logging in (we need his keys)
    # Since I don't have his password here, I'll just check what keys he has loaded in the DB
    # and if any of them can decrypt Kiki's private records.
    
    # We'll use the vault_rodolfo.db which is what Rodolfo sees.
    db_path = "data/vault_rodolfo.db"
    if not os.path.exists(db_path):
        print("Rodolfo's vault not found.")
        return

    # To actually verify if he SEES the password, we need to know what keys he has.
    # I'll check the 'get_all' results directly as if it were the UI.
    # I'll use a hack to get the sm instance as if Rodolfo were logged in.
    # Note: I'll need to know Rodolfo's password if I wanted to use SM directly, 
    # but I can inspect the logic and data.
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Check if there are private records from other users
    target_user = "RODOLFO" # Current user
    private_others = conn.execute("SELECT * FROM secrets WHERE owner_name != ? AND is_private = 1", (target_user,)).fetchall()
    
    if not private_others:
        print("No private records from others found in Rodolfo's vault. (This is good/expected)")
    else:
        print(f"CRITICAL: Found {len(private_others)} private records from other users in Rodolfo's vault!")
        for r in private_others:
            print(f"Svc: {r['service']}, Owner: {r['owner_name']}, Private: {r['is_private']}")

    conn.close()

if __name__ == "__main__":
    verify_privacy_breach()
