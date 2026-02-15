import sqlite3
import os
import requests
import json

URL = "https://htktaodjjxfsqsqedylu.supabase.co"
KEY = "sb_publishable_wokz-BbGYIvuc4Kvaz3qXg_vrkmg_yA"

def fix_kiki_access_v2():
    data_dir = "c:\\PassGuardian_v2\\data"
    db_path = os.path.join(data_dir, "vault_kiki.db")
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Get user info
    cur.execute("SELECT user_id, vault_id, protected_key FROM users LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("No user info in local DB")
        return
    
    u_id, v_id, p_key = row
    p_key_hex = p_key.hex() if isinstance(p_key, bytes) else p_key
    
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    # Trial and error for column names based on common patterns in this project
    # Some tables use 'wrapped_master_key', others 'wrapped_vault_key'
    payload = {
        "user_id": u_id,
        "vault_id": v_id,
        "wrapped_master_key": p_key_hex
    }
    
    print(f"Trying payload: {list(payload.keys())}")
    r = requests.post(f"{URL}/rest/v1/vault_access", headers=headers, data=json.dumps(payload))
    if r.status_code in (200, 201, 204):
        print("SUCCESS!")
    else:
        print(f"FAILED: {r.status_code} - {r.text}")
        if "wrapped_master_key" in r.text:
            print("Retrying with 'wrapped_vault_key'...")
            payload["wrapped_vault_key"] = payload.pop("wrapped_master_key")
            r = requests.post(f"{URL}/rest/v1/vault_access", headers=headers, data=json.dumps(payload))
            if r.status_code in (200, 201, 204):
                print("SUCCESS (v2)!")
            else:
                print(f"FAILED AGAIN: {r.status_code} - {r.text}")

    conn.close()

if __name__ == "__main__":
    fix_kiki_access_v2()
