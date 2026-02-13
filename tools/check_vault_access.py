import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def check_vault_access():
    print(">>> Checking vault_access...")
    res = supabase.table("vault_access").select("*").limit(5).execute()
    if res.data:
        print(f"Columns: {res.data[0].keys()}")
        for r in res.data:
            print(r)
    else:
        print("No vault_access records found.")

if __name__ == "__main__":
    check_vault_access()
