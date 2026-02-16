import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def check_rodolfo():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: No se encontraron las credenciales de Supabase.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("--- CLOUD PROFILE (users) ---")
    res = supabase.table("users").select("*").ilike("username", "RODOLFO").execute()
    if res.data:
        p = res.data[0]
        print(f"Username: {p['username']}")
        print(f"User ID: {p['id']}")
        print(f"Vault Salt: {p.get('vault_salt')}")
        print(f"Vault ID: {p.get('vault_id')}")
        print(f"Wrapped Local: {len(p.get('wrapped_vault_key') or '')} chars")
        
        u_id = p['id']
        print("\n--- CLOUD VAULT ACCESS ---")
        res_va = supabase.table("vault_access").select("*").eq("user_id", u_id).execute()
        for va in res_va.data:
            print(f"Vault ID: {va['vault_id']} | Key Len: {len(va.get('wrapped_master_key') or '')} chars | Access: {va.get('access_level')}")
    else:
        print("User RODOLFO not found in cloud.")

if __name__ == "__main__":
    check_rodolfo()
