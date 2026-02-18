# -*- coding: utf-8 -*-
"""
Create Test User: ARGON2_TEST

This script creates a test user with Argon2 password hash.
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from src.infrastructure.crypto_engine import CryptoEngine
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import uuid
from datetime import datetime

def create_argon2_test_user():
    """Create test user with Argon2 hash"""
    
    print("\n" + "="*60)
    print("Creating Test User: ARGON2_TEST")
    print("="*60)
    
    # User details
    username = "ARGON2_TEST"
    password = "TestPassword123!"
    vault_id = str(uuid.uuid4())
    
    try:
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if user already exists
        result = supabase.table("users").select("username").eq("username", username).execute()
        if result.data:
            print(f"[INFO] User '{username}' already exists")
            print("[INFO] Deleting existing user...")
            supabase.table("users").delete().eq("username", username).execute()
            print("[OK] Existing user deleted")
        
        # Generate Argon2 hash
        print("\n[STEP 1] Generating Argon2 password hash...")
        hash_result, salt = CryptoEngine.hash_user_password_auto(password)
        
        algorithm = 'Argon2' if hash_result.startswith('$argon2') else 'PBKDF2'
        print(f"[OK] Algorithm: {algorithm}")
        print(f"[OK] Hash: {hash_result[:60]}...")
        print(f"[OK] Salt: {salt.hex() if salt else '(embedded in hash)'}")
        
        if not hash_result.startswith('$argon2'):
            print("\n[ERROR] Expected Argon2 hash but got PBKDF2!")
            print("[ERROR] Check config/crypto_config.py settings")
            return False
        
        # Generate vault master key
        print("\n[STEP 2] Generating vault master key...")
        vault_master_key = CryptoEngine.generate_vault_master_key()
        print(f"[OK] Vault key generated: {len(vault_master_key)} bytes")
        
        # Wrap vault key with password
        print("\n[STEP 3] Wrapping vault key with password...")
        
        # For Argon2, we use a deterministic salt derived from the password hash
        # This ensures the same vault key can be unwrapped later
        import hashlib
        vault_salt = hashlib.sha256(hash_result.encode()).digest()[:16]
        
        # wrap_vault_key expects (vault_key, password_string, salt)
        wrapped_blob = CryptoEngine.wrap_vault_key(vault_master_key, password, vault_salt)
        
        # Extract nonce and ciphertext
        nonce = wrapped_blob[:12]
        wrapped_key = wrapped_blob[12:]
        
        print(f"[OK] Vault key wrapped ({len(wrapped_blob)} bytes total)")
        
        # Create user record
        print("\n[STEP 4] Creating user in Supabase...")
        
        user_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "password_hash": hash_result,
            "salt": salt.hex() if salt else "",  # Empty for Argon2
            "vault_id": vault_id,
            "role": "secondary",
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        print(f"[INFO] User data prepared (minimal schema)")
        print(f"[INFO] Username: {username}")
        print(f"[INFO] Vault ID: {vault_id}")
        print(f"[INFO] Hash algorithm: Argon2")
        
        result = supabase.table("users").insert(user_data).execute()
        
        if result.data:
            print(f"[OK] User created successfully!")
            print(f"[OK] User ID: {user_data['id']}")
            print(f"[OK] Vault ID: {vault_id}")
            
            # Verify hash format
            print("\n[STEP 5] Verifying hash format...")
            stored_hash = result.data[0]['password_hash']
            print(f"[OK] Stored hash: {stored_hash[:60]}...")
            print(f"[OK] Format: {'Argon2' if stored_hash.startswith('$argon2') else 'PBKDF2'}")
            
            # Test verification
            print("\n[STEP 6] Testing password verification...")
            is_valid = CryptoEngine.verify_user_password_auto(password, None, stored_hash)
            print(f"[OK] Verification: {is_valid}")
            
            if is_valid:
                print("\n" + "="*60)
                print("[SUCCESS] Test user created successfully!")
                print("="*60)
                print(f"\nCredentials:")
                print(f"  Username: {username}")
                print(f"  Password: {password}")
                print(f"\nNext steps:")
                print(f"  1. Logout from current session")
                print(f"  2. Login with ARGON2_TEST / TestPassword123!")
                print(f"  3. Verify dashboard loads correctly")
                return True
            else:
                print("\n[ERROR] Password verification failed!")
                return False
        else:
            print("[ERROR] Failed to create user")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_argon2_test_user()
    sys.exit(0 if success else 1)
