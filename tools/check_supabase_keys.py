import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def check_supabase_keys():
    print(">>> Checking Supabase for RODOLFO...")
    # 1. Get User ID
    res = supabase.table("users").select("id, username, password_hash, salt, vault_id").eq("username", "RODOLFO").execute()
    if not res.data:
        print("User RODOLFO not found in Supabase.")
        return
    
    user = res.data[0]
    print(f"User ID: {user['id']}")
    print(f"Vault ID: {user['vault_id']}")
    
    # 2. Get Vault Access
    res_acc = supabase.table("vault_access").select("*").eq("user_id", user['id']).execute()
    if res_acc.data:
        for acc in res_acc.data:
            print(f"Vault Access: Vault {acc['vault_id']}, Key Length: {len(acc['wrapped_master_key']) if acc['wrapped_master_key'] else 0}")
    else:
        print("No vault access found in Supabase.")

if __name__ == "__main__":
    check_supabase_keys()
