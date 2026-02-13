import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def check_rodolfo_cloud_profile():
    print(">>> Checking RODOLFO in Supabase...")
    res = supabase.table("users").select("id, username, role").ilike("username", "RODOLFO").execute()
    if res.data:
        print(f"Profile: {res.data[0]}")
    else:
        print("Profile not found.")

if __name__ == "__main__":
    check_rodolfo_cloud_profile()
