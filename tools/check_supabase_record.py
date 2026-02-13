import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def check_record_109():
    print(">>> Checking Record 109 in Supabase...")
    res = supabase.table("secrets").select("*").ilike("service", "RODOLFO 3").execute()
    if res.data:
        for r in res.data:
            print(f"ID: {r['id']}, Service: {r['service']}, Owner: {r['owner_name']}, Private: {r['is_private']}")
    else:
        print("Record 'RODOLFO 3' not found in Supabase.")

if __name__ == "__main__":
    check_record_109()
