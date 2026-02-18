# -*- coding: utf-8 -*-
"""
REVERT: Restore ARGON2_TEST to original vault
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY

def revert_argon2_vault():
    """Revert ARGON2_TEST back to original vault"""
    
    print("\n" + "="*60)
    print("REVERTING: ARGON2_TEST to Original Vault")
    print("="*60)
    
    original_vault_id = "18f18ab4-df5b-4fa0-bcd2-5fb83ff1bf4a"
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Update vault_id back to original
        print(f"\n[STEP 1] Reverting vault_id to: {original_vault_id}")
        result = supabase.table("users").update({
            "vault_id": original_vault_id
        }).eq("username", "ARGON2_TEST").execute()
        
        if result.data:
            print(f"[OK] Vault ID reverted")
        else:
            print(f"[ERROR] Failed to revert")
            return False
        
        # Remove shared vault access
        print(f"\n[STEP 2] Removing shared vault access...")
        shared_vault_id = "4fd73bb9-95cf-4350-9f8e-33ad9d31aaae"
        
        user_result = supabase.table("users").select("id").eq("username", "ARGON2_TEST").execute()
        user_id = user_result.data[0]['id']
        
        delete_result = supabase.table("vault_access").delete().eq("user_id", user_id).eq("vault_id", shared_vault_id).execute()
        print(f"[OK] Shared vault access removed")
        
        print("\n" + "="*60)
        print("[SUCCESS] ARGON2_TEST reverted to original state")
        print("="*60)
        print(f"\nUser now has:")
        print(f"  - Own vault: {original_vault_id}")
        print(f"  - No shared vault access")
        print(f"  - Original cryptographic keys intact")
        print(f"\nTry login now - should work!")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = revert_argon2_vault()
    sys.exit(0 if success else 1)
