# -*- coding: utf-8 -*-
"""
Grant ARGON2_TEST access to shared vault (IT SECURITY)
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY

def grant_shared_vault_access():
    """Grant ARGON2_TEST access to RODOLFO's shared vault"""
    
    print("\n" + "="*60)
    print("Granting ARGON2_TEST Access to Shared Vault")
    print("="*60)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get ARGON2_TEST user
        print("\n[STEP 1] Fetching ARGON2_TEST user...")
        user_result = supabase.table("users").select("*").eq("username", "ARGON2_TEST").execute()
        
        if not user_result.data:
            print("[ERROR] ARGON2_TEST not found")
            return False
        
        argon_user = user_result.data[0]
        argon_user_id = argon_user['id']
        
        print(f"[OK] User ID: {argon_user_id}")
        
        # Get RODOLFO's vault (IT SECURITY)
        print("\n[STEP 2] Finding shared vault (IT SECURITY)...")
        rodolfo_result = supabase.table("users").select("vault_id").eq("username", "RODOLFO").execute()
        
        if not rodolfo_result.data:
            print("[ERROR] RODOLFO not found")
            return False
        
        shared_vault_id = rodolfo_result.data[0]['vault_id']
        print(f"[OK] Shared Vault ID: {shared_vault_id}")
        
        # Get RODOLFO's wrapped_master_key from vault_access
        print("\n[STEP 3] Getting vault master key...")
        rodolfo_user_result = supabase.table("users").select("id").eq("username", "RODOLFO").execute()
        rodolfo_user_id = rodolfo_user_result.data[0]['id']
        
        vault_access_result = supabase.table("vault_access").select("wrapped_master_key").eq("user_id", rodolfo_user_id).eq("vault_id", shared_vault_id).execute()
        
        if not vault_access_result.data:
            print("[ERROR] No vault_access found for RODOLFO")
            return False
        
        wrapped_master_key = vault_access_result.data[0]['wrapped_master_key']
        print(f"[OK] Wrapped master key retrieved")
        
        # Check if ARGON2_TEST already has access
        print("\n[STEP 4] Checking existing access...")
        existing_access = supabase.table("vault_access").select("*").eq("user_id", argon_user_id).eq("vault_id", shared_vault_id).execute()
        
        if existing_access.data:
            print("[INFO] Access already exists, updating...")
            update_result = supabase.table("vault_access").update({
                "wrapped_master_key": wrapped_master_key
            }).eq("user_id", argon_user_id).eq("vault_id", shared_vault_id).execute()
            
            if update_result.data:
                print("[OK] Access updated")
            else:
                print("[ERROR] Failed to update access")
                return False
        else:
            print("[INFO] Creating new access entry...")
            access_data = {
                "user_id": argon_user_id,
                "vault_id": shared_vault_id,
                "wrapped_master_key": wrapped_master_key
            }
            
            insert_result = supabase.table("vault_access").insert(access_data).execute()
            
            if insert_result.data:
                print("[OK] Access granted")
            else:
                print("[ERROR] Failed to grant access")
                return False
        
        # Update ARGON2_TEST's vault_id to shared vault
        print("\n[STEP 5] Updating user's vault_id...")
        update_user = supabase.table("users").update({
            "vault_id": shared_vault_id
        }).eq("username", "ARGON2_TEST").execute()
        
        if update_user.data:
            print("[OK] User vault_id updated")
        else:
            print("[ERROR] Failed to update vault_id")
            return False
        
        print("\n" + "="*60)
        print("[SUCCESS] ARGON2_TEST now has access to shared vault!")
        print("="*60)
        print(f"\nShared Vault: {shared_vault_id}")
        print(f"User can now decrypt all secrets from RODOLFO, KIKI, PUMBA, etc.")
        print(f"\nLogout and login again to apply changes.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = grant_shared_vault_access()
    sys.exit(0 if success else 1)
