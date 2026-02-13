from supabase import create_client
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_vaults():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        # Intentar leer una tabla llamada 'vaults'
        res = supabase.table("vaults").select("*").execute()
        print(f"Data in 'vaults' table: {res.data}")
    except Exception as e:
        print(f"Table 'vaults' not found or error: {e}")

if __name__ == "__main__":
    check_vaults()
