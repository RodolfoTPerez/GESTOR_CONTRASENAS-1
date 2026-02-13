
import requests
import time
from config.config import SUPABASE_URL, SUPABASE_KEY

def test_insert():
    url = f"{SUPABASE_URL}/rest/v1/security_audit"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    payload = {
        "timestamp": int(time.time()),
        "user_name": "DEBUG_TEST",
        "action": "INSERT_TEST",
        "status": "SUCCESS",
        "details": "Checking if user_id is required"
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_insert()
