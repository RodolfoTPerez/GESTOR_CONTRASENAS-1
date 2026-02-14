
import sys
import os
import sqlite3
import secrets
import getpass
import base64
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

def unwrap_key(wrapped_key: bytes, password: str, salt: bytes, iterations: int = 100000) -> bytes:
    kek = derive_kek(password, salt, iterations)
    nonce = wrapped_key[:12]
    ciphertext = wrapped_key[12:]
    return AESGCM(kek).decrypt(nonce, ciphertext, None)

def wrap_key(key: bytes, password: str, salt: bytes) -> bytes:
    kek = derive_kek(password, salt)
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(kek).encrypt(nonce, key, None)

print("="*80)
print("🛡️  VULTRAX CORE - ULTIMATE RECOVERY & RESET TOOL (V5.0)")
print("="*80)
print("\n[!] PREPARING DIAGNOSTICS...")

username = "RODOLFO".upper()
db_path = Path(f"data/vault_{username.lower()}.db")

if not db_path.exists():
    print(f"[-] FATAL: Database not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
if not user:
    print(f"[-] FATAL: User {username} not found in database.")
    sys.exit(1)

v_salt = bytes(user['vault_salt']) if user['vault_salt'] else None
w_key = bytes(user['wrapped_vault_key']) if user['wrapped_vault_key'] else None
v_id = user['vault_id']

print(f"[+] USER DETECTED: {username}")
print(f"[+] VAULT ID: {v_id}")
print(f"[+] SALT STATUS: {'PRESENT' if v_salt else 'MISSING'}")
print(f"[+] KEY STATUS: {'PRESENT' if w_key else 'MISSING'}")

print("\n" + "-"*40)
print("Option 1: DATA RECOVERY (Safe)")
print("   Rescues your existing vault key using an OLD password.")
print("   Maintains access to all shared secrets.")
print("-"*40)
print("Option 2: DESTRUCTIVE RESET (Scorched Earth)")
print("   Generates a NEW vault key with your CURRENT password.")
print("   YOU WILL LOSE ACCESS TO ALL EXISTING SECRETS IN THIS VAULT.")
print("-"*40)

mode = input("\nSelect Mode (RECOVERY/RESET): ").strip().upper()

if mode == "RECOVERY":
    print("\n[RECOVERY] Please enter the password that WAS working before the lockout:")
    old_pass = getpass.getpass("Old Password: ")
    print("[RECOVERY] Please enter your CURRENT login password:")
    new_pass = getpass.getpass("Current Password: ")

    # Try common iterations
    success = False
    for iters in [100000, 50000, 10000]:
        try:
            print(f"[*] Attempting unwrap with {iters} iterations...")
            rescued_key = unwrap_key(w_key, old_pass, v_salt, iterations=iters)
            print(f"[!] SUCCESS! Vault key rescued with {iters} iterations.")
            
            print("[*] Re-encrypting with CURRENT password...")
            new_wrap = wrap_key(rescued_key, new_pass, v_salt)
            
            cursor.execute("UPDATE users SET wrapped_vault_key=? WHERE username=?", (sqlite3.Binary(new_wrap), username))
            cursor.execute("INSERT OR REPLACE INTO vault_access (user_id, vault_id, wrapped_master_key, role) VALUES (?, ?, ?, 'admin')",
                           (user['id'], v_id, sqlite3.Binary(new_wrap)))
            conn.commit()
            print("[+] DATABASE UPDATED. You can now login normally.")
            success = True
            break
        except Exception: continue
    
    if not success:
        print("[-] FAILED: Could not recover key with those credentials. Data is still locked.")

elif mode == "RESET":
    print("\n" + "!"*40)
    print("WARNING: THIS WILL DELETE ACCESS TO ALL EXISTING SECRETS")
    print("Confirm by typing 'I UNDERSTAND':")
    confirm = input("> ")
    if confirm != "I UNDERSTAND":
        print("[-] Aborted.")
        sys.exit(0)

    print("\n[RESET] Enter your CURRENT login password to seal the new key:")
    curr_pass = getpass.getpass("Password: ")
    
    new_key = secrets.token_bytes(32)
    new_wrap = wrap_key(new_key, curr_pass, v_salt or secrets.token_bytes(16))
    
    cursor.execute("UPDATE users SET wrapped_vault_key=? WHERE username=?", (sqlite3.Binary(new_wrap), username))
    cursor.execute("INSERT OR REPLACE INTO vault_access (user_id, vault_id, wrapped_master_key, role) VALUES (?, ?, ?, 'admin')",
                   (user['id'], v_id, sqlite3.Binary(new_wrap)))
    conn.commit()
    print("[+] RESET COMPLETE. You can now login, but the vault is EMPTY (encrypted with new key).")

else:
    print("[-] Invalid selection.")

conn.close()
print("\nDone. Restart the app and login.")
