import sqlite3
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

blob_hex = "445f5b68089cbe67356a284fbc52ff9af04f1a7aeb83804fcd9bb601245d10b1e252928c44e84be25a9e467138cf188dcd757f69b91c3467de3af5fb"
blob = bytes.fromhex(blob_hex)
nonce = blob[:12]
ciphertext = blob[12:]

password = input("Enter current password: ") if False else "RODOLFO123" # I don't know the password, but I can try common ones or just run it as a tool if I had it.

# Actually, I'll just gather all salts and try them.
salts = [
    bytes.fromhex("cc245e8313b3cad85acaf947af2bc235"), # RODOLFO's current salt
    b"public_salt",
    b"salt_123",
    b"RODOLFO",
    b"rodolfo",
    b"RODOLFO".upper(),
    b""
]

# Find more salts in DBs
dbs = [r"c:\PassGuardian_v2\data\vultrax.db", r"c:\PassGuardian_v2\data\vault_rodolfo.db"]
for db in dbs:
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        # Try metadata table
        try:
            cur = conn.execute("SELECT value FROM meta WHERE key LIKE '%salt%'")
            for r in cur.fetchall():
                salts.append(r[0])
        except: pass
        # Try users table
        try:
            cur = conn.execute("SELECT salt, vault_salt FROM users")
            for r in cur.fetchall():
                if r[0]: salts.append(r[0].encode() if isinstance(r[0], str) else r[0])
                if r[1]: salts.append(r[1])
        except: pass
        conn.close()

# Deduplicate salts
unique_salts = []
for s in salts:
    if s not in unique_salts and s is not None:
        unique_salts.append(s)

print(f"Trying {len(unique_salts)} salts...")
# I can't really brute force without the password, 
# but I can show the code that would do it.

# Wait! The user is frustrated. I should just offer a "CLEAN RESET" if they agree.
# But "borrar todos los .db" is what they said they CANNOT do? 
# No, they said "NO PUEDO BORRAR TODOS LOS .DB". 
# Maybe they meant "I can't (as in, I'm not allowed/don't want to)" or "I can't (technically)".

# Actually, if I just "RESET USER IDENTITY" through the admin method, 
# it creates a NEW personal key and NEW salt. 
# But it fails to re-wrap the vault.

# What if I "Repair" the vault record by overwriting it with a FRESH, EMPTY vault?
# No, they want their secrets.

# I'll try one more thing: use the MASTER_key from the session to derive the vault key?
# No, that's for personal secrets.

