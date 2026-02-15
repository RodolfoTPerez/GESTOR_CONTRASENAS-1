import requests
import json

URL = "https://htktaodjjxfsqsqedylu.supabase.co"
KEY = "sb_publishable_wokz-BbGYIvuc4Kvaz3qXg_vrkmg_yA"

def check_cloud_audit():
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json"
    }
    
    print("\n--- CLOUD AUDIT_LOG (KIKI) ---")
    url = f"{URL}/rest/v1/audit_log?user_name=ilike.KIKI&select=*"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    else:
        print(f"Error: {r.status_code} - {r.text}")

if __name__ == "__main__":
    check_cloud_audit()
