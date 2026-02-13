
import requests
import json
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_supabase_with_headers():
    url = f"{SUPABASE_URL}/rest/v1/secrets?select=*"
    
    # Rodolfo's info (from local db check)
    user = "RODOLFO"
    user_id = "948addcb-ec74-402e-b3af-440ae569337d"
    vault_id = "0637ae0d-7446-4c94-bc06-18c918ce596e"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "x-guardian-user": user,
        "x-guardian-user-id": user_id,
        "x-guardian-vault": vault_id,
    }
    
    print(f"Testing Supabase with headers: {json.dumps(headers, indent=2)}")
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
        return

    records = r.json()
    print(f"Found {len(records)} records in Supabase secrets table (WITH RLS HEADERS):")
    for rr in records:
        print(f"ID: {rr.get('id')}, Svc: {rr.get('service')}, User: {rr.get('username')}, Owner: {rr.get('owner_name')}")

if __name__ == "__main__":
    check_supabase_with_headers()
