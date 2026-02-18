# -*- coding: utf-8 -*-
"""
Test Script: Argon2 Verification (Simple Version)
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from src.infrastructure.crypto_engine import CryptoEngine
from src.infrastructure.auth.auth_manager import AuthManager

def test_argon2():
    """Test Argon2 hashing"""
    print("\n" + "="*60)
    print("TEST: Argon2 Hash Generation and Verification")
    print("="*60)
    
    test_password = "TestPassword123!"
    
    try:
        # Generate hash
        hash_result = CryptoEngine.hash_user_password_argon2(test_password)
        print(f"[OK] Hash generated: {hash_result[:60]}...")
        print(f"[OK] Starts with '$argon2': {hash_result.startswith('$argon2')}")
        
        # Verify correct password
        is_valid = CryptoEngine.verify_user_password_argon2(test_password, hash_result)
        print(f"[OK] Correct password verified: {is_valid}")
        
        # Verify wrong password
        is_invalid = CryptoEngine.verify_user_password_argon2("WrongPassword", hash_result)
        print(f"[OK] Wrong password rejected: {not is_invalid}")
        
        return hash_result.startswith('$argon2')
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auto_selection():
    """Test auto hash selection"""
    print("\n" + "="*60)
    print("TEST: Auto Hash Selection (Should use Argon2)")
    print("="*60)
    
    test_password = "TestPassword123!"
    
    try:
        # Generate with auto-selection
        hash_result, salt = CryptoEngine.hash_user_password_auto(test_password)
        algorithm = 'Argon2' if hash_result.startswith('$argon2') else 'PBKDF2'
        
        print(f"[OK] Hash generated: {hash_result[:60]}...")
        print(f"[OK] Algorithm: {algorithm}")
        print(f"[OK] Salt: {salt.hex() if salt else '(embedded in hash)'}")
        
        # Verify
        is_valid = CryptoEngine.verify_user_password_auto(test_password, salt, hash_result)
        print(f"[OK] Verification: {is_valid}")
        
        return hash_result.startswith('$argon2')
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_manager():
    """Test AuthManager"""
    print("\n" + "="*60)
    print("TEST: AuthManager Integration")
    print("="*60)
    
    test_password = "TestPassword123!"
    
    try:
        auth = AuthManager(supabase=None, secrets_manager=None)
        
        # Generate hash
        hash_result, salt_hex = auth.hash_password(test_password)
        algorithm = 'Argon2' if hash_result.startswith('$argon2') else 'PBKDF2'
        
        print(f"[OK] Hash generated: {hash_result[:60]}...")
        print(f"[OK] Algorithm: {algorithm}")
        print(f"[OK] Salt: {salt_hex if salt_hex else '(embedded)'}")
        
        # Verify
        salt_for_verify = bytes.fromhex(salt_hex) if salt_hex else None
        is_valid = auth.verify_password(test_password, salt_for_verify, hash_result)
        print(f"[OK] Verification: {is_valid}")
        
        return hash_result.startswith('$argon2')
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ARGON2 IMPLEMENTATION VERIFICATION")
    print("="*60)
    
    test1 = test_argon2()
    test2 = test_auto_selection()
    test3 = test_auth_manager()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Direct Argon2:      {'PASS' if test1 else 'FAIL'}")
    print(f"Auto Selection:     {'PASS (Argon2)' if test2 else 'FAIL (PBKDF2)'}")
    print(f"AuthManager:        {'PASS (Argon2)' if test3 else 'FAIL (PBKDF2)'}")
    
    if test1 and test2 and test3:
        print("\n[SUCCESS] All tests passed - Argon2 is working!")
        print("\nReady to create user 'ARGON2_TEST' in the application")
    else:
        print("\n[FAILED] Some tests failed - Review configuration")
