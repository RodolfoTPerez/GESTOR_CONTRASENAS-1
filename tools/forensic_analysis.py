from supabase import create_client
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def forensic_schema_analysis():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Lista de todas las tablas que el sistema usa o podría usar
    tables = ["users", "vaults", "secrets", "invitations", "vault_access", "security_audit", "audit_log"]
    
    print("=== PASSGUARDIAN: ANALISIS FORENSE DE ESQUEMA SUPABASE ===\n")
    
    for table in tables:
        print(f"--- Inspecting Table: {table} ---")
        try:
            # Consultamos un registro (limit 0 para ver estructura si la API lo permite)
            # O simplemente intentamos un select de columnas clave
            res = supabase.table(table).select("*").limit(1).execute()
            if len(res.data) >= 0:
                print(f"✅ Table exists.")
                if res.data:
                    print(f"   Structure: {list(res.data[0].keys())}")
                else:
                    print(f"   Structure: (Empty table, testing key columns...)")
                    # Prueba de fuego de columnas críticas
                    key_cols = ["id", "vault_id", "created_at"]
                    for col in key_cols:
                        try:
                            supabase.table(table).select(col).limit(1).execute()
                            print(f"      - '{col}': OK")
                        except:
                            print(f"      - '{col}': MISSING or TYPE MISMATCH")
        except Exception as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                print(f"❌ Table DOES NOT EXIST.")
            else:
                print(f"⚠️ Error accessing table: {e}")
        print("-" * 40)

if __name__ == "__main__":
    forensic_schema_analysis()
