
import sqlite3
import os
import requests
import json
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_local_pumba():
    data_dir = r"C:\PassGuardian_v2\data"
    print("Searching for 'PUMBA' in local databases...")
    for filename in os.listdir(data_dir):
        if filename.startswith("vault_") and filename.endswith(".db"):
            db_path = os.path.join(data_dir, filename)
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # Check for table 'secrets' or whatever it is called
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='secrets'")
                if cursor.fetchone():
                    cursor.execute("SELECT id, service, username, owner_name FROM secrets WHERE service LIKE '%PUMBA%'")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"[{filename}] Found {len(rows)} records:")
                        for r in rows:
                            print(f"  ID: {r[0]} | Service: {r[1]} | Username: {r[2]} | Owner: {r[3]}")
                conn.close()
            except Exception as e:
                print(f"Error checking {filename}: {e}")

def check_cloud_pumba():
    print("\nSearching for 'PUMBA' in cloud (Supabase)...")
    url = f"{SUPABASE_URL}/rest/v1/secrets?service=ilike.*PUMBA*&select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            secrets = r.json()
            print(f"Found {len(secrets)} records in cloud:")
            for s in secrets:
                print(f"  ID: {s.get('id')} | Service: {s.get('service')} | Username: {s.get('username')} | Owner: {s.get('owner_name')} | Deleted: {s.get('deleted')}")
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_local_pumba()
    check_cloud_pumba()
