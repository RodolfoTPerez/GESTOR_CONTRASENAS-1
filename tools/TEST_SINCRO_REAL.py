from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR) + "/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def probar_sincronizacion():
    print("--- TEST DE CAPACIDAD DE ESCRITURA (RODOLFO) ---")
    
    # 1. Obtener el ID de Rodolfo
    print("Buscando ID de RODOLFO...")
    res_user = supabase.table("users").select("id, vault_id").eq("username", "RODOLFO").execute()
    
    if not res_user.data:
        print("ERROR: No se encontró al usuario RODOLFO en la tabla 'users'.")
        return
    
    user_id = res_user.data[0]['id']
    vault_id = res_user.data[0]['vault_id']
    print(f"ID detectado: {user_id}")
    print(f"Vault detectado: {vault_id}")

    # 2. Intentar un insert de prueba
    print("\nIntentando insertar secreto de prueba para validar RLS...")
    test_secret = {
        "owner_id": user_id,
        "vault_id": vault_id,
        "username": "test_sync",
        "notes": "Validación de políticas RLS"
    }
    
    try:
        res_ins = supabase.table("secrets").insert(test_secret).execute()
        print("¡ÉXITO! El secreto se insertó correctamente. La nube ya acepta tus datos.")
        
        # 3. Limpiar el test
        print("Limpiando secreto de prueba...")
        supabase.table("secrets").delete().eq("username", "test_sync").execute()
        print("Todo limpio.")
        
    except Exception as e:
        print(f"FALLO DE ESCUDO (401/42501): {e}")
        print("\nSi el error es 'new row violates RLS', la política SQL no se aplicó correctamente.")

if __name__ == "__main__":
    probar_sincronizacion()
