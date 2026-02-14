
import sys
import os
from pathlib import Path
import base64

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.database.db_manager import DBManager
from src.infrastructure.repositories.user_repo import UserRepository
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.crypto_engine import CryptoEngine
import sqlite3

def test_password_rotation():
    print("--- Testing Password Change Key Rotation ---")
    
    username = "TEST_USER"
    old_pwd = "old_password_123"
    new_pwd = "new_password_456"
    
    # 1. Setup initial state
    data_dir = Path("data")
    if not data_dir.exists(): data_dir.mkdir()
    
    db = DBManager("test_rotation")
    sm = SecretsManager()
    sm.users = UserRepository(db)
    
    # Mocking session
    sm.session.current_user = username
    sm.session.current_user_id = "user-123"
    sm.session.current_vault_id = "vault-abc"
    sm.session.user_role = "admin"
    sm.session.personal_key = os.urandom(32)
    
    vault_master_key = os.urandom(32)
    
    # Save initial profile with old password
    v_salt = os.urandom(16)
    wrapped_v_key = CryptoEngine.wrap_vault_key(vault_master_key, old_pwd, v_salt)
    
    hash_old, salt_old = CryptoEngine.hash_user_password(old_pwd)
    protected_key_old = sm.security.wrap_key(sm.session.personal_key, old_pwd, v_salt)
    
    sm.save_local_user_profile(
        username, hash_old, salt_old.hex(), v_salt, 
        vault_id="vault-abc", 
        role="admin", 
        protected_key=protected_key_old,
        wrapped_vault_key=wrapped_v_key,
        user_id="user-123"
    )
    
    # Populate vault_access table
    sm.users.save_vault_access("vault-abc", wrapped_v_key, "admin")
    
    print("Initial state setup with old password.")
    
    # 2. Perform password change
    print(f"Changing password to: {new_pwd}")
    # We pass user_manager=None to avoid Supabase calls in this local test
    sm.change_login_password(old_pwd, new_pwd, user_manager=None)
    
    # 3. Verify results
    print("\n--- Verification ---")
    
    # Check new profile
    profile = sm.get_local_user_profile(username)
    new_v_salt = profile.get("vault_salt")
    new_wrapped_vault_key = profile.get("wrapped_vault_key")
    
    # Verify we can decrypt with NEW password
    try:
        decrypted_v_key = CryptoEngine.unwrap_vault_key(new_wrapped_vault_key, new_pwd, new_v_salt)
        if decrypted_v_key == vault_master_key:
            print("SUCCESS: Vault key in 'users' table re-encrypted correctly.")
        else:
            print("FAIL: Vault key mismatch in 'users' table.")
    except Exception as e:
        print(f"FAIL: Could not decrypt vault key with new password: {e}")

    # Verify vault_access table
    access = sm.users.get_vault_access("vault-abc")
    new_vault_access_key = access['wrapped_master_key']
    
    try:
        decrypted_va_key = CryptoEngine.unwrap_vault_key(new_vault_access_key, new_pwd, new_v_salt)
        if decrypted_va_key == vault_master_key:
            print("SUCCESS: Vault key in 'vault_access' table re-encrypted correctly.")
        else:
            print("FAIL: Vault key mismatch in 'vault_access' table.")
    except Exception as e:
        print(f"FAIL: Could not decrypt vault_access key with new password: {e}")

    print("\n--- Test Finished ---")
    db.close()
    if os.path.exists(db.db_path):
        os.remove(db.db_path)

if __name__ == "__main__":
    test_password_rotation()
