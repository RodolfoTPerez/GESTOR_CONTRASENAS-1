import os
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
res = s.table('secrets').select('id').execute()
print(f"Total Secrets in Cloud: {len(res.data)}")
