# -*- coding: utf-8 -*-
"""
Debug ARGON2_TEST Password Verification
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.crypto_engine import CryptoEngine

def debug_password_verification():
    """Debug why password verification is failing"""
    
    print("\n" + "="*60)
    print("Debugging ARGON2_TEST Password Verification")
    print("="*60)
    
    username = "ARGON2_TEST"
    password = "TestPassword123!"
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get user from Supabase
        print("\n[STEP 1] Fetching user from Supabase...")
        result = supabase.table("users").select("*").eq("username", username).execute()
        
        if not result.data:
            print(f"[ERROR] User not found")
            return False
        
        user = result.data[0]
        
        print(f"[OK] User found")
        print(f"  Username: {user['username']}")
        print(f"  Password hash: {user['password_hash'][:60]}...")
        print(f"  Salt: {user.get('salt', 'N/A')}")
        print(f"  Vault ID: {user['vault_id']}")
        print(f"  Protected key exists: {bool(user.get('protected_key'))}")
        print(f"  Vault salt exists: {bool(user.get('vault_salt'))}")
        
        # Check hash format
        password_hash = user['password_hash']
        is_argon2 = password_hash.startswith('$argon2')
        
        print(f"\n[STEP 2] Hash format analysis...")
        print(f"  Algorithm: {'Argon2' if is_argon2 else 'PBKDF2'}")
        
        if is_argon2:
            print(f"  Hash format: {password_hash[:80]}...")
        else:
            print(f"  Hash format: {password_hash[:40]}... (hex)")
        
        # Test verification
        print(f"\n[STEP 3] Testing password verification...")
        
        salt = user.get('salt', '')
        salt_bytes = bytes.fromhex(salt) if salt else None
        
        try:
            result = CryptoEngine.verify_user_password_auto(password, salt_bytes, password_hash)
            print(f"  Verification result: {result}")
            
            if result:
                print(f"[SUCCESS] Password verification works!")
            else:
                print(f"[ERROR] Password verification failed")
                
                # Try direct Argon2 verification
                if is_argon2:
                    print(f"\n[STEP 4] Trying direct Argon2 verification...")
                    direct_result = CryptoEngine.verify_user_password_argon2(password, password_hash)
                    print(f"  Direct Argon2 result: {direct_result}")
                    
                    if direct_result:
                        print(f"[INFO] Direct Argon2 works, but auto-detection fails")
                        print(f"[INFO] Possible issue with salt parameter")
                
        except Exception as e:
            print(f"[ERROR] Verification exception: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_password_verification()
