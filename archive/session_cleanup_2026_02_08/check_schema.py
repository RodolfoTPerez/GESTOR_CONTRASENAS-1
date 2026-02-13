
import requests
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_schema():
    url = f"{SUPABASE_URL}/rest/v1/security_audit?select=*&limit=1"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Prefer": "return=representation"
    }
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200 and r.json():
            print("Columns found in security_audit:")
            print(list(r.json()[0].keys()))
        else:
            print(f"Error or no data: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_schema()
