
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.database.db_manager import DBManager
from src.infrastructure.repositories.user_repo import UserRepository
from src.infrastructure.secrets_manager import SecretsManager
import sqlite3

def test_vault_access():
    print("--- Verifying vault_access implementation ---")
    
    # 1. Initialize DB and check schema
    db = DBManager("test_vault")
    print(f"DB initialized at: {db.db_path}")
    
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vault_access'")
    if cur.fetchone():
        print("Table 'vault_access' exists.")
    else:
        print("Table 'vault_access' MISSING.")
        return
        
    # 2. Test UserRepository methods
    repo = UserRepository(db)
    vault_id = "test-vault-uuid-001"
    key_blob = b"this_is_a_test_wrapped_key_32bytes"
    
    print("\n--- Testing UserRepository ---")
    success = repo.save_vault_access(vault_id, key_blob, "admin")
    if success:
        print("save_vault_access successful.")
    else:
        print("save_vault_access failed.")
        
    access = repo.get_vault_access(vault_id)
    if access and access['vault_id'] == vault_id:
        print(f"get_vault_access successful. Vault ID: {access['vault_id']}")
    else:
        print(f"get_vault_access failed or returned wrong data: {access}")
        
    all_access = repo.get_all_vault_accesses()
    if len(all_access) >= 1:
        print(f"get_all_vault_accesses successful. Count: {len(all_access)}")
    else:
        print("get_all_vault_accesses failed.")
        
    # 3. Test legacy update method
    print("\n--- Testing Legacy Update Integration ---")
    success = repo.update_vault_access("RODOLFO", "active-vault-uuid", b"wrapped_active_key")
    if success:
        print("update_vault_access successful (legacy + new table).")
        # Check if it's in the new table too
        check = repo.get_vault_access("active-vault-uuid")
        if check:
            print("Verified: access also persisted in 'vault_access' table.")
        else:
            print("Error: access NOT found in 'vault_access' table after legacy update.")
    else:
        print("update_vault_access failed.")
        
    print("\n--- Verification Complete ---")
    db.close()
    
    # Cleanup test DB if needed
    # os.remove(db.db_path)

if __name__ == "__main__":
    test_vault_access()
