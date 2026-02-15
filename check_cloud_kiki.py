import requests
import json

URL = "https://htktaodjjxfsqsqedylu.supabase.co"
KEY = "sb_publishable_wokz-BbGYIvuc4Kvaz3qXg_vrkmg_yA"

def check_cloud_kiki():
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json"
    }
    
    print("\n--- CLOUD USERS (KIKI) ---")
    url = f"{URL}/rest/v1/users?username=ilike.KIKI&select=*"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {r.status_code} - {r.text}")

    print("\n--- CLOUD VAULT_ACCESS (KIKI) ---")
    if r.status_code == 200 and data:
        u_id = data[0].get("id")
        print(f"User ID: {u_id}")
        url_va = f"{URL}/rest/v1/vault_access?user_id=eq.{u_id}&select=*"
        r_va = requests.get(url_va, headers=headers)
        if r_va.status_code == 200:
            print(json.dumps(r_va.json(), indent=2))
        else:
            print(f"VA Error: {r_va.status_code} - {r_va.text}")

if __name__ == "__main__":
    check_cloud_kiki()
