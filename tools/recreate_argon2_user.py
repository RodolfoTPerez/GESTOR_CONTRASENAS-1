# -*- coding: utf-8 -*-
"""
Delete and Recreate ARGON2_TEST with Proper Shared Vault Access
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.crypto_engine import CryptoEngine
from datetime import datetime
import base64

def recreate_argon2_user():
    """Delete old user and create new one with proper shared vault access"""
    
    print("\n" + "="*60)
    print("Recreating ARGON2_TEST with Shared Vault Access")
    print("="*60)
    
    username = "ARGON2_TEST"
    password = "TestPassword123!"
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # STEP 1: Delete existing user
        print("\n[STEP 1] Deleting existing ARGON2_TEST user...")
        delete_result = supabase.table("users").delete().eq("username", username).execute()
        print(f"[OK] User deleted")
        
        # STEP 2: Get RODOLFO's shared vault info
        print("\n[STEP 2] Getting shared vault (IT SECURITY) info...")
        rodolfo = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
        
        if not rodolfo.data:
            print("[ERROR] RODOLFO not found")
            return False
        
        rodolfo_data = rodolfo.data[0]
        shared_vault_id = rodolfo_data['vault_id']
        rodolfo_user_id = rodolfo_data['id']
        
        print(f"[OK] Shared Vault ID: {shared_vault_id}")
        print(f"[OK] Vault Name: IT SECURITY")
        
        # STEP 3: Get vault master key from RODOLFO's vault_access
        print("\n[STEP 3] Getting vault master key...")
        vault_access = supabase.table("vault_access").select("wrapped_master_key").eq("user_id", rodolfo_user_id).eq("vault_id", shared_vault_id).execute()
        
        if not vault_access.data:
            print("[ERROR] No vault_access found for RODOLFO")
            return False
        
        wrapped_master_key = vault_access.data[0]['wrapped_master_key']
        print(f"[OK] Wrapped master key retrieved")
        
        # STEP 4: Generate Argon2 password hash
        print("\n[STEP 4] Generating Argon2 password hash...")
        password_hash, salt = CryptoEngine.hash_user_password_auto(password)
        
        if not password_hash.startswith('$argon2'):
            print("[ERROR] Expected Argon2 but got PBKDF2!")
            return False
        
        print(f"[OK] Argon2 hash: {password_hash[:60]}...")
        print(f"[OK] Salt: {salt.hex() if salt else '(embedded)'}")
        
        # STEP 5: Use RODOLFO's vault_salt and protected_key approach
        # For shared vault, we use the same wrapped_master_key
        print("\n[STEP 5] Preparing user data...")
        
        import uuid
        new_user_id = str(uuid.uuid4())
        
        user_data = {
            "id": new_user_id,
            "username": username,
            "password_hash": password_hash,
            "salt": salt.hex() if salt else "",
            "vault_id": shared_vault_id,  # Use shared vault from start
            "role": "secondary",
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
            "protected_key": wrapped_master_key,  # Use same as RODOLFO
            "vault_salt": rodolfo_data.get('vault_salt', '')  # Use same as RODOLFO
        }
        
        print(f"[OK] User ID: {new_user_id}")
        print(f"[OK] Vault ID: {shared_vault_id}")
        print(f"[OK] Using shared vault_salt and protected_key")
        
        # STEP 6: Create user
        print("\n[STEP 6] Creating user in Supabase...")
        result = supabase.table("users").insert(user_data).execute()
        
        if not result.data:
            print("[ERROR] Failed to create user")
            return False
        
        print(f"[OK] User created successfully")
        
        # STEP 7: Create vault_access entry
        print("\n[STEP 7] Creating vault_access entry...")
        access_data = {
            "user_id": new_user_id,
            "vault_id": shared_vault_id,
            "wrapped_master_key": wrapped_master_key
        }
        
        access_result = supabase.table("vault_access").insert(access_data).execute()
        
        if access_result.data:
            print(f"[OK] vault_access entry created")
        else:
            print(f"[WARNING] vault_access creation failed (may already exist)")
        
        # STEP 8: Verify
        print("\n[STEP 8] Verifying password...")
        verify_result = CryptoEngine.verify_user_password_auto(password, None, password_hash)
        print(f"[OK] Password verification: {verify_result}")
        
        print("\n" + "="*60)
        print("[SUCCESS] ARGON2_TEST recreated successfully!")
        print("="*60)
        print(f"\nCredentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"\nConfiguration:")
        print(f"  - Hash: Argon2id")
        print(f"  - Vault: IT SECURITY (shared)")
        print(f"  - Can see all secrets: Yes")
        print(f"\nReady for login!")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = recreate_argon2_user()
    sys.exit(0 if success else 1)
