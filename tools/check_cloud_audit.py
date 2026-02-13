
import requests
import json
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_audit_logs():
    url = f"{SUPABASE_URL}/rest/v1/security_audit?select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        logs = r.json()
        print(f"Found {len(logs)} audit logs in cloud.")
        users = set(l.get("user_name") for l in logs)
        print(f"Users with logs: {users}")
        for l in logs[:10]:
            print(f"TS: {l.get('timestamp')}, User: {l.get('user_name')}, Action: {l.get('action')}")
    else:
        print(f"Error: {r.status_code} - {r.text}")

if __name__ == "__main__":
    check_audit_logs()
