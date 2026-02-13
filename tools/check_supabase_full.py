from supabase import create_client
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def check_supabase_users_detail():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        # Consultar todas las columnas disponibles
        res = supabase.table("users").select("*").execute()
        print(f"Users found in Supabase: {res.data}")
        
        res_v = supabase.table("vaults").select("*").execute()
        print(f"Vaults found in Supabase: {res_v.data}")
    except Exception as e:
        print(f"Error checking Supabase: {e}")

if __name__ == "__main__":
    check_supabase_users_detail()
