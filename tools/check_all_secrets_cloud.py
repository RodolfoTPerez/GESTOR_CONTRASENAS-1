import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def check_kiki_records_cloud():
    print(">>> Checking secrets in Supabase...")
    res = supabase.table("secrets").select("id, service, owner_name, is_private").execute()
    if res.data:
        for r in res.data:
            print(f"ID: {r['id']}, Service: {r['service']}, Owner: {r['owner_name']}, Private: {r['is_private']}")
    else:
        print("No secrets found in Supabase (or blocked by RLS).")

if __name__ == "__main__":
    check_kiki_records_cloud()
