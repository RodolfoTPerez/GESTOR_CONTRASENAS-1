# -*- coding: utf-8 -*-
"""
Fix ARGON2_TEST User: Create Vault and Activate Permissions
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

def fix_argon2_test_user():
    """Fix vault and permissions for ARGON2_TEST"""
    
    print("\n" + "="*60)
    print("Fixing ARGON2_TEST User: Vault & Permissions")
    print("="*60)
    
    username = "ARGON2_TEST"
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get user
        print("\n[STEP 1] Fetching user...")
        result = supabase.table("users").select("*").eq("username", username).execute()
        
        if not result.data:
            print(f"[ERROR] User '{username}' not found")
            return False
        
        user = result.data[0]
        vault_id = user['vault_id']
        user_id = user['id']
        
        print(f"[OK] User: {username}")
        print(f"[OK] User ID: {user_id}")
        print(f"[OK] Vault ID: {vault_id}")
        
        # Check if vault exists
        print("\n[STEP 2] Checking vault...")
        vault_result = supabase.table("vaults").select("*").eq("id", vault_id).execute()
        
        if not vault_result.data:
            print(f"[INFO] Vault {vault_id} does not exist, creating...")
            
            # Create vault with minimal fields
            vault_data = {
                "id": vault_id,
                "name": f"{username} Vault",
                "created_at": datetime.utcnow().isoformat()
            }
            
            create_result = supabase.table("vaults").insert(vault_data).execute()
            
            if create_result.data:
                print(f"[OK] Vault created: {vault_id}")
            else:
                print(f"[ERROR] Failed to create vault")
                return False
        else:
            print(f"[OK] Vault already exists: {vault_id}")
        
        # Activate user
        print("\n[STEP 3] Activating user...")
        update_result = supabase.table("users").update({
            "active": True
        }).eq("username", username).execute()
        
        if update_result.data:
            print(f"[OK] User activated")
        else:
            print(f"[ERROR] Failed to activate user")
            return False
        
        # Create vault_access entry
        print("\n[STEP 4] Creating vault_access entry...")
        
        # Check if entry exists
        access_result = supabase.table("vault_access").select("*").eq("user_id", user_id).eq("vault_id", vault_id).execute()
        
        if not access_result.data:
            access_data = {
                "user_id": user_id,
                "vault_id": vault_id,
                "wrapped_master_key": user.get("protected_key", "")
            }
            
            access_insert = supabase.table("vault_access").insert(access_data).execute()
            
            if access_insert.data:
                print(f"[OK] vault_access entry created")
            else:
                print(f"[ERROR] Failed to create vault_access")
                return False
        else:
            print(f"[OK] vault_access entry already exists")
        
        print("\n" + "="*60)
        print("[SUCCESS] User fixed successfully!")
        print("="*60)
        print(f"\nUser '{username}' is now ready:")
        print(f"  - Vault created: {vault_id}")
        print(f"  - User activated: True")
        print(f"  - vault_access configured")
        print(f"\nTry logging in again!")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_argon2_test_user()
    sys.exit(0 if success else 1)
