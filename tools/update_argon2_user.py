# -*- coding: utf-8 -*-
"""
Update ARGON2_TEST User with Complete Fields

This script updates the test user with all required fields for proper functionality.
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from src.infrastructure.crypto_engine import CryptoEngine
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import base64
import hashlib

def update_argon2_test_user():
    """Update test user with complete fields"""
    
    print("\n" + "="*60)
    print("Updating ARGON2_TEST User with Complete Fields")
    print("="*60)
    
    username = "ARGON2_TEST"
    password = "TestPassword123!"
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get existing user
        print("\n[STEP 1] Fetching existing user...")
        result = supabase.table("users").select("*").eq("username", username).execute()
        
        if not result.data:
            print(f"[ERROR] User '{username}' not found")
            return False
        
        user = result.data[0]
        print(f"[OK] User found: {user['username']}")
        print(f"[OK] Vault ID: {user['vault_id']}")
        
        # Generate vault master key
        print("\n[STEP 2] Generating vault master key...")
        vault_master_key = CryptoEngine.generate_vault_master_key()
        print(f"[OK] Vault key: {len(vault_master_key)} bytes")
        
        # Derive salt from hash for consistency
        password_hash = user['password_hash']
        vault_salt = hashlib.sha256(password_hash.encode()).digest()[:16]
        
        # Wrap vault key
        print("\n[STEP 3] Wrapping vault key...")
        wrapped_blob = CryptoEngine.wrap_vault_key(vault_master_key, password, vault_salt)
        nonce = wrapped_blob[:12]
        wrapped_key = wrapped_blob[12:]
        
        print(f"[OK] Wrapped: {len(wrapped_blob)} bytes total")
        
        # Prepare update data
        print("\n[STEP 4] Preparing complete user data...")
        
        update_data = {
            "protected_key": base64.b64encode(wrapped_blob).decode('ascii'),
            "vault_salt": base64.b64encode(vault_salt).decode('ascii')
        }
        
        print(f"[OK] protected_key: {update_data['protected_key'][:40]}...")
        print(f"[OK] vault_salt: {update_data['vault_salt']}")
        
        # Update user
        print("\n[STEP 5] Updating user in Supabase...")
        result = supabase.table("users").update(update_data).eq("username", username).execute()
        
        if result.data:
            print(f"[OK] User updated successfully!")
            
            # Verify
            print("\n[STEP 6] Verifying update...")
            verify_result = supabase.table("users").select("username, protected_key, vault_salt").eq("username", username).execute()
            
            if verify_result.data:
                v_user = verify_result.data[0]
                print(f"[OK] Username: {v_user['username']}")
                print(f"[OK] protected_key exists: {bool(v_user.get('protected_key'))}")
                print(f"[OK] vault_salt exists: {bool(v_user.get('vault_salt'))}")
                
                print("\n" + "="*60)
                print("[SUCCESS] User updated with complete fields!")
                print("="*60)
                print(f"\nCredentials:")
                print(f"  Username: {username}")
                print(f"  Password: {password}")
                print(f"\nReady for login test!")
                return True
            else:
                print("[ERROR] Verification failed")
                return False
        else:
            print("[ERROR] Update failed")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_argon2_test_user()
    sys.exit(0 if success else 1)
