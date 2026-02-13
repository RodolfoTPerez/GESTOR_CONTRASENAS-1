
import requests
import json
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_supabase():
    url = f"{SUPABASE_URL}/rest/v1/secrets?select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    # Trying without custom headers first to see EVERYTHING (bypassing RLS if we use service key, 
    # but here we use anon key probably)
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
        return

    records = r.json()
    print(f"Found {len(records)} records in Supabase secrets table:")
    for rr in records:
        print(f"ID: {rr.get('id')}, Svc: {rr.get('service')}, User: {rr.get('username')}, Owner: {rr.get('owner_name')}, Private: {rr.get('is_private')}, Vault: {rr.get('vault_id')}")

if __name__ == "__main__":
    check_supabase()
