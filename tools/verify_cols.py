from supabase import create_client
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def verify_columns():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    cols_to_check = ["owner_name", "is_private", "vault_id"]
    for col in cols_to_check:
        try:
            supabase.table("secrets").select(col).limit(1).execute()
            print(f"Columna '{col}' existe.")
        except Exception as e:
            print(f"Columna '{col}' NO detectada o error: {e}")

if __name__ == "__main__":
    verify_columns()
