import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def check_vault_members():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    v_id = "a8e77bff-27da-4bfe-84bf-1efafc07ec71"
    
    print(f"--- MEMBERS OF VAULT {v_id} ---")
    res = supabase.table("vault_access").select("user_id, access_level, updated_at").eq("vault_id", v_id).execute()
    for m in res.data:
        u_id = m['user_id']
        u_res = supabase.table("users").select("username").eq("id", u_id).execute()
        username = u_res.data[0]['username'] if u_res.data else "Unknown"
        print(f"User: {username} ({u_id}) | Level: {m['access_level']} | Updated: {m['updated_at']}")

if __name__ == "__main__":
    check_vault_members()
