import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar cliente Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL o SUPABASE_KEY no encontrados en .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def revelar():
    print("--- INSPECCIÓN DE COLUMNAS (SISTEMA GUARDIÁN) ---")
    tablas = ["users", "vaults", "vault_groups", "secrets"]
    for t in tablas:
        print(f"\n" + "="*40)
        print(f"TABLA: {t}")
        print("="*40)
        
        # 1. Intentar obtener un registro para ver las columnas
        try:
            res = supabase.table(t).select("*").limit(1).execute()
            if res.data:
                print(f"Columnas detectadas (via data): {list(res.data[0].keys())}")
            else:
                print("Estado: Tabla vacía. Intentando detectar mediante error de insert...")
                
                # 2. Forzar error de tipo para descubrir el tipo de dato del ID y las columnas requeridas
                try:
                    # Usamos un valor absurdo para forzar el error de sintaxis/tipo
                    supabase.table(t).insert({"id": "TEST_TIPO_ID_ABSURDO"}).execute()
                except Exception as e_inner:
                    err_msg = str(e_inner)
                    print(f"Respuesta de la DB: {err_msg}")
                    
        except Exception as e_outer:
            print(f"Error al acceder a {t}: {e_outer}")

if __name__ == "__main__":
    revelar()
