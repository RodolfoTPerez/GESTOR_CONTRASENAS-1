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

res = s.table('users').select('id, username, vault_id').eq('username', 'RODOLFO').execute()
print(res.data)
