import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def check_supabase_schema():
    print(">>> Checking Supabase 'secrets' columns...")
    # Just try to select all columns and see what we get
    res = supabase.table("secrets").select("*").limit(1).execute()
    if res.data:
        print(f"Columns: {res.data[0].keys()}")
    else:
        print("No records to check columns.")

if __name__ == "__main__":
    check_supabase_schema()
