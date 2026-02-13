
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.config.path_manager import PathManager

def test_no_db_creation():
    print("Testing DB creation prevention...")
    
    # Ensure we are starting from a clean state for the test user
    test_user = "nonexistentuserXYZ"
    db_path = PathManager.get_user_db(test_user)
    if db_path.exists():
        os.remove(db_path)
    
    print(f"Target DB path: {db_path}")
    
    # Initialize Managers
    sm = SecretsManager()
    um = UserManager(sm)
    
    # Scenario: prepare_for_user (happens on username entry or try_login)
    print(f"Calling prepare_for_user('{test_user}')...")
    um.prepare_for_user(test_user)
    
    if db_path.exists():
        print(f"FAIL: Database created prematurely at {db_path} during prepare_for_user")
        return False
    else:
        print("SUCCESS: No database created during prepare_for_user.")

    # Scenario: validate_user_access (happens during login)
    print(f"Calling validate_user_access('{test_user}')...")
    res = um.validate_user_access(test_user)
    
    if db_path.exists():
        print(f"FAIL: Database created prematurely at {db_path} during validate_user_access")
        return False
    else:
        print("SUCCESS: No database created during validate_user_access.")

    print("\nVerified: No DB files created for non-existent users.")
    return True

if __name__ == "__main__":
    try:
        if test_no_db_creation():
            print("\nALL TESTS PASSED")
            sys.exit(0)
        else:
            print("\nTESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR DURING VERIFICATION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
