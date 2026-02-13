from supabase import create_client
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def list_all_tables():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        # No hay una forma directa de listar tablas vía PostgREST sin RPC o inspección de esquema
        # Pero podemos intentar leer las tablas conocidas y ver si hay alguna nueva
        known_tables = ["users", "secrets", "vault_access", "invitations", "security_audit", "audit_log"]
        for table in known_tables:
            try:
                res = supabase.table(table).select("count", count="exact").limit(1).execute()
                print(f"Table '{table}' exists (count: {res.count})")
            except:
                print(f"Table '{table}' NOT found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_tables()
