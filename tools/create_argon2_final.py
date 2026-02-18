# -*- coding: utf-8 -*-
"""
Final Fix: Create ARGON2_TEST with proper protected_key
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.crypto_engine import CryptoEngine
from datetime import datetime
import uuid
import base64
import os

def create_argon2_user_final():
    """Create ARGON2_TEST with proper protected_key encrypted with its own password"""
    
    print("\n" + "="*60)
    print("Final Fix: Creating ARGON2_TEST with Proper Keys")
    print("="*60)
    
    username = "ARGON2_TEST"
    password = "TestPassword123!"
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Delete existing user
        print("\n[STEP 1] Deleting existing user...")
        supabase.table("users").delete().eq("username", username).execute()
        print("[OK] User deleted")
        
        # Get RODOLFO's vault info
        print("\n[STEP 2] Getting shared vault info...")
        rodolfo = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
        rodolfo_data = rodolfo.data[0]
        shared_vault_id = rodolfo_data['vault_id']
        rodolfo_user_id = rodolfo_data['id']
        
        print(f"[OK] Shared Vault ID: {shared_vault_id}")
        
        # Get the ACTUAL vault master key (unwrapped)
        print("\n[STEP 3] Getting vault master key from RODOLFO...")
        vault_access = supabase.table("vault_access").select("wrapped_master_key").eq("user_id", rodolfo_user_id).eq("vault_id", shared_vault_id).execute()
        
        rodolfo_wrapped_key = vault_access.data[0]['wrapped_master_key']
        print(f"[OK] RODOLFO's wrapped key retrieved")
        
        # Generate Argon2 hash for ARGON2_TEST
        print("\n[STEP 4] Generating Argon2 password hash...")
        password_hash, salt = CryptoEngine.hash_user_password_auto(password)
        print(f"[OK] Argon2 hash: {password_hash[:60]}...")
        
        # Generate vault_salt for ARGON2_TEST (derived from Argon2 hash)
        print("\n[STEP 5] Generating vault_salt...")
        import hashlib
        vault_salt_bytes = hashlib.sha256(password_hash.encode('utf-8')).digest()[:16]
        vault_salt_b64 = base64.b64encode(vault_salt_bytes).decode('utf-8')
        print(f"[OK] Vault salt: {vault_salt_b64}")
        
        # Generate a personal key for ARGON2_TEST
        print("\n[STEP 6] Generating personal encryption key...")
        personal_key = os.urandom(32)  # 256-bit key
        print(f"[OK] Personal key generated ({len(personal_key)} bytes)")
        
        # Wrap personal key with KEK derived from ARGON2_TEST's password
        print("\n[STEP 7] Wrapping personal key...")
        wrapped_personal_key = CryptoEngine.wrap_vault_key(
            vault_master_key=personal_key,
            user_password=password,
            user_salt=vault_salt_bytes
        )
        protected_key_b64 = base64.b64encode(wrapped_personal_key).decode('utf-8')
        print(f"[OK] Protected key: {protected_key_b64[:40]}...")
        
        # Create user
        print("\n[STEP 8] Creating user...")
        new_user_id = str(uuid.uuid4())
        
        user_data = {
            "id": new_user_id,
            "username": username,
            "password_hash": password_hash,
            "salt": salt.hex() if salt else "",
            "vault_id": shared_vault_id,
            "role": "secondary",
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
            "protected_key": protected_key_b64,  # OWN protected_key
            "vault_salt": vault_salt_b64  # OWN vault_salt
        }
        
        result = supabase.table("users").insert(user_data).execute()
        print(f"[OK] User created")
        
        # Create vault_access with RODOLFO's wrapped key
        print("\n[STEP 9] Creating vault_access with shared vault key...")
        access_data = {
            "user_id": new_user_id,
            "vault_id": shared_vault_id,
            "wrapped_master_key": rodolfo_wrapped_key  # Use RODOLFO's key for shared vault
        }
        
        supabase.table("vault_access").insert(access_data).execute()
        print(f"[OK] vault_access created")
        
        print("\n" + "="*60)
        print("[SUCCESS] ARGON2_TEST created with proper keys!")
        print("="*60)
        print(f"\nCredentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"\nKey Structure:")
        print(f"  - protected_key: Own key encrypted with own password")
        print(f"  - vault_access.wrapped_master_key: Shared vault key")
        print(f"  - vault_salt: Derived from Argon2 hash")
        print(f"\nReady for login!")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_argon2_user_final()
    sys.exit(0 if success else 1)
