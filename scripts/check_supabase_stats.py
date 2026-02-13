
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_project_stats():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: No se encontraron las credenciales de Supabase.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    tables = ["users", "secrets", "invitations", "vault_access", "vault_groups", "security_audit"]
    
    print("="*60)
    print(" ESTADÍSTICAS DE DATOS EN SUPABASE - PASSGUARDIAN")
    print("="*60)
    
    total_records = 0
    
    for table in tables:
        try:
            # Usamos count='exact' para obtener el número total de filas
            response = supabase.table(table).select("*", count='exact').limit(0).execute()
            count = response.count if response.count is not None else 0
            print(f" -> Tabla {table.ljust(15)}: {count} registros")
            total_records += count
        except Exception as e:
            print(f" -> Tabla {table.ljust(15)}: Error al consultar ({str(e)[:50]}...)")

    print("-" * 60)
    print(f" TOTAL DE REGISTROS EN LA NUBE: {total_records}")
    print("="*60)
    print("\nNota: El tamaño en disco (MB/GB) solo es visible desde el")
    print("Panel de Control de Supabase (Database -> Settings).")

if __name__ == "__main__":
    get_project_stats()
