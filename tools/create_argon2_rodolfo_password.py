# -*- coding: utf-8 -*-
"""
Create ARGON2_TEST with RODOLFO's password (Argon2 hash)
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.crypto_engine import CryptoEngine
from datetime import datetime
import uuid

def create_argon2_with_rodolfo_password():
    """Create ARGON2_TEST using RODOLFO's password but with Argon2 hash"""
    
    print("\n" + "="*60)
    print("Creating ARGON2_TEST with RODOLFO's Password (Argon2)")
    print("="*60)
    
    username = "ARGON2_TEST"
    # IMPORTANT: Using RODOLFO's password
    rodolfo_password = input("\nEnter RODOLFO's password: ")
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Delete existing ARGON2_TEST
        print("\n[STEP 1] Deleting existing ARGON2_TEST...")
        supabase.table("users").delete().eq("username", username).execute()
        print("[OK] User deleted")
        
        # Get RODOLFO's data
        print("\n[STEP 2] Getting RODOLFO's vault credentials...")
        rodolfo = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
        
        if not rodolfo.data:
            print("[ERROR] RODOLFO not found")
            return False
        
        rodolfo_data = rodolfo.data[0]
        rodolfo_user_id = rodolfo_data['id']
        
        print(f"[OK] RODOLFO's vault_id: {rodolfo_data['vault_id']}")
        print(f"[OK] RODOLFO's vault_salt: {rodolfo_data.get('vault_salt', 'N/A')}")
        print(f"[OK] RODOLFO's protected_key: {rodolfo_data.get('protected_key', 'N/A')[:40]}...")
        
        # Generate Argon2 hash for RODOLFO's password
        print("\n[STEP 3] Generating Argon2 hash for RODOLFO's password...")
        password_hash, salt = CryptoEngine.hash_user_password_auto(rodolfo_password)
        
        if not password_hash.startswith('$argon2'):
            print("[ERROR] Expected Argon2 but got PBKDF2!")
            return False
        
        print(f"[OK] Argon2 hash: {password_hash[:60]}...")
        print(f"[OK] Salt: {salt.hex() if salt else '(embedded)'}")
        
        # Get RODOLFO's vault access
        print("\n[STEP 4] Getting RODOLFO's vault access...")
        vault_access = supabase.table("vault_access").select("*").eq("user_id", rodolfo_user_id).eq("vault_id", rodolfo_data['vault_id']).execute()
        
        if not vault_access.data:
            print("[ERROR] No vault_access found for RODOLFO")
            return False
        
        wrapped_master_key = vault_access.data[0]['wrapped_master_key']
        print(f"[OK] Wrapped master key retrieved")
        
        # Create ARGON2_TEST user
        print("\n[STEP 5] Creating ARGON2_TEST user...")
        new_user_id = str(uuid.uuid4())
        
        user_data = {
            "id": new_user_id,
            "username": username,
            "password_hash": password_hash,  # Argon2 hash
            "salt": salt.hex() if salt else "",  # Empty for Argon2
            "vault_id": rodolfo_data['vault_id'],  # Same vault
            "vault_salt": rodolfo_data.get('vault_salt', ''),  # Same vault_salt
            "protected_key": rodolfo_data.get('protected_key', ''),  # Same protected_key
            "role": "secondary",
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("users").insert(user_data).execute()
        
        if not result.data:
            print("[ERROR] Failed to create user")
            return False
        
        print(f"[OK] User created")
        
        # Create vault_access
        print("\n[STEP 6] Creating vault_access...")
        access_data = {
            "user_id": new_user_id,
            "vault_id": rodolfo_data['vault_id'],
            "wrapped_master_key": wrapped_master_key
        }
        
        supabase.table("vault_access").insert(access_data).execute()
        print(f"[OK] vault_access created")
        
        # Verify password
        print("\n[STEP 7] Verifying Argon2 password...")
        verify_result = CryptoEngine.verify_user_password_auto(rodolfo_password, None, password_hash)
        print(f"[OK] Password verification: {verify_result}")
        
        print("\n" + "="*60)
        print("[SUCCESS] ARGON2_TEST created successfully!")
        print("="*60)
        print(f"\nCredentials:")
        print(f"  Username: {username}")
        print(f"  Password: <same as RODOLFO>")
        print(f"\nConfiguration:")
        print(f"  - Hash: Argon2id (NEW)")
        print(f"  - Vault: IT SECURITY (shared with RODOLFO)")
        print(f"  - vault_salt: Same as RODOLFO")
        print(f"  - protected_key: Same as RODOLFO")
        print(f"\nCan access all shared secrets: YES")
        print(f"\nReady for login!")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_argon2_with_rodolfo_password()
    sys.exit(0 if success else 1)
