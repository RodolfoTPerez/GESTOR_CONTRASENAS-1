from supabase import create_client
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_final_status():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    tables = ["users", "vaults", "invitations", "secrets", "security_audit"]
    
    print("=== PASSGUARDIAN: FINAL SYSTEM STATUS ===\n")
    
    for table in tables:
        try:
            res = supabase.table(table).select("*").limit(1).execute()
            print(f"Table '{table}': EXISTS (Count: {len(res.data)})")
            if res.data:
                print(f"   Sample columns: {list(res.data[0].keys())}")
        except Exception as e:
            print(f"Table '{table}': ERROR/MISSING -> {e}")
        print("-" * 30)

    # Specific check for Rodolfo's vault
    try:
        user_res = supabase.table("users").select("username, vault_id, linked_hwid").eq("username", "RODOLFO").execute()
        if user_res.data:
            u = user_res.data[0]
            v_id = u.get('vault_id')
            print(f"RODOLFO Status:")
            print(f" - Vault ID: {v_id}")
            print(f" - HWID: {u.get('linked_hwid')}")
            
            if v_id:
                v_res = supabase.table("vaults").select("name").eq("id", v_id).execute()
                if v_res.data:
                    print(f" - Vault Name in Cloud: {v_res.data[0].get('name')}")
    except Exception as e:
        print(f"Error checking Rodolfo: {e}")

if __name__ == "__main__":
    check_final_status()
