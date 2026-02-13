from supabase import create_client
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_orphans():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        res = supabase.table("secrets").select("count", count="exact").execute()
        print(f"Total secrets in Supabase: {res.count}")
    except Exception as e:
        print(f"Error checking secrets: {e}")

if __name__ == "__main__":
    check_orphans()
