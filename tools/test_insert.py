from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_insert():
    payload = {
        "username": "TEST_ADMIN",
        "role": "admin",
        "active": True
    }
    try:
        print(f"Attempting to insert into 'users' table...")
        res = supabase.table("users").insert(payload).execute()
        print(f"Insert success: {res.data}")
    except Exception as e:
        print(f"Insert failed: {e}")

if __name__ == "__main__":
    test_insert()
