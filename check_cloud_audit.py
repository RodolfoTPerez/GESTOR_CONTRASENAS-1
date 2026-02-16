import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def check_audit():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("--- RECENT AUDIT LOGS FOR RODOLFO ---")
    res = supabase.table("security_audit")\
        .select("*")\
        .ilike("user_name", "RODOLFO")\
        .order("timestamp", desc=True)\
        .limit(20)\
        .execute()
    
    for log in res.data:
        print(f"[{log.get('timestamp')}] Action: {log.get('action')} | Status: {log.get('status')} | Details: {log.get('details')}")

if __name__ == "__main__":
    check_audit()
