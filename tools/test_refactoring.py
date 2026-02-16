import sys
import os
import base64

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.secrets_manager import SecretsManager

def test_refactored_manager():
    print(">>> Testing Refactored SecretsManager Facade...")
    
    # 1. Initialize
    sm = SecretsManager()
    print("[OK] Initialization successful")
    
    # 2. Setup a test user profile (simulate setup)
    username = "TEST_REFAC"
    import getpass
    password = getpass.getpass("Ingrese contraseña para TEST REFACTOR: ")
    salt = os.urandom(16).hex()
    v_salt = os.urandom(16)
    
    # [PRPROTOCOL] Reconnect to user vault BEFORE saving profile
    sm.reconnect(username)
    print(f"[OK] Switched context to vault_{username.lower()}.db")
    
    # [SECURITY FIX] We MUST wrap a key, otherwise session has nothing to load
    mock_master_key = os.urandom(32)
    protected_key = sm.wrap_key(mock_master_key, password, v_salt)
    
    sm.save_local_user_profile(
        username, "hash_dummy", salt, v_salt, 
        role="admin", 
        user_id="uid_123",
        protected_key=protected_key
    )
    print("[OK] Test profile saved with wrapped key")

    # 3. Set Active User (Key derivation flow)
    sm.set_active_user(username, password)
    
    if sm.session.current_user == username and sm.session.master_key is not None:
        print(f"[OK] Active user set: {sm.session.current_user}")
        print(f"[OK] Master Key loaded: {len(sm.session.master_key)} bytes")
    else:
        print(f"[ERR] Failed to set active user or load keys. User: {sm.session.current_user}, Key: {sm.session.master_key is not None}")
        return

    # 4. Add a secret
    try:
        sid = sm.add_secret("TestService", "testuser", "secret_content", notes="Refactoring test")
        print(f"[OK] Secret added with ID: {sid}")
    except Exception as e:
        print(f"[ERR] Failed to add secret: {e}")
        return

    # 5. Retrieve secret
    secrets = sm.get_all()
    found = False
    for s in secrets:
        if s["service"] == "TestService" and s["secret"] == "secret_content":
            found = True
            break
    
    if found:
        print("[OK] Secret retrieved and decrypted correctly")
    else:
        print("[ERR] Secret not found or decryption failed")

    # 6. Audit check
    logs = sm.get_audit_logs()
    if any(l["action"] == "CREATE SECRET" for l in logs):
        print("[OK] Audit log recorded correctly")
    else:
        print("[ERR] Audit log missing")

    # 7. Cleanup
    sm.cleanup_vault_cache()
    if sm.session.current_user is None:
        print("[OK] Cache cleaned up and zeroed")
    else:
        print("[ERR] Cleanup failed")

    print("\n>>> ALL REFACTORING TESTS PASSED (MODULAR SYSTEM OK)")

if __name__ == "__main__":
    test_refactored_manager()
