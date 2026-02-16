import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
from unittest.mock import MagicMock

def test_key_logic():
    print("Testing UserManager key logic...")
    
    # Mock Sm and Supabase
    sm = SecretsManager()
    sm.master_key = b"A" * 32
    sm.current_vault_id = "test-vault-id"
    
    um = UserManager(sm)
    um.supabase = MagicMock()
    
    # Test get_master_vault_id
    vid = um.get_master_vault_id()
    print(f"Master Vault ID: {vid}")
    assert vid == "test-vault-id"
    
    # Test _generate_user_keys
    # Should inherit from sm.master_key
    keys = um._generate_user_keys("TESTUSER", "user", "testpassword")
    print(f"Keys generated: {keys.keys()}")
    assert keys['protected'] is not None
    assert keys['vault_id'] == "test-vault-id"
    
    # Verify unwrap
    from src.infrastructure.crypto_engine import CryptoEngine
    unwrapped = CryptoEngine.unwrap_vault_key(keys['protected'], "testpassword", keys['v_salt'])
    assert unwrapped == sm.master_key
    print("Key inheritance and wrapping VERIFIED.")

if __name__ == "__main__":
    try:
        test_key_logic()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
