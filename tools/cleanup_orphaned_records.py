# -*- coding: utf-8 -*-
"""
Clean up orphaned ARGON2_TEST records
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY

def cleanup_orphaned_records():
    """Delete orphaned records from old ARGON2_TEST user"""
    
    print("\n" + "="*60)
    print("Cleaning Up Orphaned ARGON2_TEST Records")
    print("="*60)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get current ARGON2_TEST user
        print("\n[STEP 1] Getting current ARGON2_TEST user...")
        user_result = supabase.table("users").select("*").eq("username", "ARGON2_TEST").execute()
        
        if not user_result.data:
            print("[ERROR] ARGON2_TEST not found")
            return False
        
        current_user = user_result.data[0]
        current_vault_id = current_user['vault_id']
        
        print(f"[OK] Current user vault: {current_vault_id}")
        print(f"[OK] Expected: 4fd73bb9-95cf-4350-9f8e-33ad9d31aaae (IT SECURITY)")
        
        # Find orphaned records (vault_id doesn't match current vault)
        print("\n[STEP 2] Finding orphaned records...")
        
        # Get all secrets in the old vault (18f18ab4-df5b-4fa0-bcd2-5fb83ff1bf4a)
        old_vault_id = "18f18ab4-df5b-4fa0-bcd2-5fb83ff1bf4a"
        
        orphaned_result = supabase.table("secrets").select("*").eq("vault_id", old_vault_id).execute()
        
        if not orphaned_result.data:
            print("[INFO] No orphaned records found")
            return True
        
        orphaned = orphaned_result.data
        
        print(f"[INFO] Found {len(orphaned)} orphaned records in old vault")
        
        # Delete orphaned records
        print("\n[STEP 3] Deleting orphaned records...")
        for secret in orphaned:
            print(f"  - Deleting: {secret.get('service', 'Unknown')} (ID: {secret['id'][:8]}...)")
            supabase.table("secrets").delete().eq("id", secret['id']).execute()
        
        print(f"[OK] Deleted {len(orphaned)} orphaned records")
        
        print("\n" + "="*60)
        print("[SUCCESS] Cleanup completed!")
        print("="*60)
        print(f"\nOrphaned records deleted: {len(orphaned)}")
        print(f"\nARGON2_TEST can now create new records in the shared vault.")
        print(f"Refresh the dashboard to see the changes.")
        
        return True
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = cleanup_orphaned_records()
    sys.exit(0 if success else 1)
