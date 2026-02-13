from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR) + "/.env")
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
s = create_client(url, key)

print("--- CLOUD SECRETS STATUS ---")
res = s.table('secrets').select('id, service, username, owner_name, deleted').execute()
deleted_records = [r for r in res.data if r['deleted']]
print(f"Total Deleted Secrets in Cloud: {len(deleted_records)}")
for r in deleted_records:
    print(r)

print(f"\nTotal: {len(res.data)}")
