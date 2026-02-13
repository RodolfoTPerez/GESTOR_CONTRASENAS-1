from supabase import create_client
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_extra_tables():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    tables = ["vaults", "vault_groups"]
    for table in tables:
        try:
            res = supabase.table(table).select("count", count="exact").limit(1).execute()
            print(f"Table '{table}' exists (count: {res.count})")
        except Exception as e:
            print(f"Table '{table}' NOT found or Error: {e}")

if __name__ == "__main__":
    check_extra_tables()
