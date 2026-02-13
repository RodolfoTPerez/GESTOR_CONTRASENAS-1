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

print("--- CLOUD SECRETS SCHEMA (Sample Record) ---")
res = s.table('secrets').select('*').limit(1).execute()
if res.data:
    print(res.data[0].keys())
else:
    print("No records found.")
