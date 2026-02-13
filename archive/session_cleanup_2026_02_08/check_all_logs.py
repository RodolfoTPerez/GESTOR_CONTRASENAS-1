
import requests
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_all_logs():
    url = f"{SUPABASE_URL}/rest/v1/security_audit?select=*&order=timestamp.desc"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            logs = r.json()
            print(f"Total logs in cloud: {len(logs)}")
            for log in logs:
                if "UPDATE PASSWORD" in str(log.get("action")) or "AGREGAR" in str(log.get("action")):
                    print(f"FOUND: TS: {log.get('timestamp')} | User: {log.get('user_name')} | Action: {log.get('action')} | Details: {log.get('details')}")
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_all_logs()
