
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def check_invitations():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Supabase credentials not found.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        r = supabase.table("invitations").select("*").execute()
        data = r.data or []
        
        print(f"\nTotal invitations found: {len(data)}")
        unused = [i for i in data if not i.get("used")]
        used = [i for i in data if i.get("used")]
        
        print(f"Unused (Visible): {len(unused)}")
        print(f"Used (Hidden): {len(used)}")
        
        for i in data:
            print(f"- Code: {i.get('code')} | Role: {i.get('role')} | Used: {i.get('used')} | Created: {i.get('created_at')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_invitations()
