import os
import sys
import base64
import secrets
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Configuración de rutas
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def nuclear_repair(password):
    print("\n" + "="*60)
    print(f"REPARACIÓN NUCLEAR PARA: RODOLFO")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Obtener IDs
    res = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
    if not res.data:
        print("Error: No se encontró al usuario.")
        return
    
    user_data = res.data[0]
    user_id = user_data['id']
    vault_id = user_data['vault_id']
    
    print(">>> Generando nueva base de seguridad (Master Key + Salt)...")
    from src.infrastructure.crypto_engine import CryptoEngine
    
    # Nueva infraestructura
    new_v_salt = secrets.token_bytes(16)
    new_master_key = secrets.token_bytes(32)
    
    # Envoltura con el password actual
    print(f">>> Envolviendo llaves con el password proporcionado...")
    try:
        protected_key = CryptoEngine.wrap_vault_key(new_master_key, password, new_v_salt)
        
        # 2. Hashear password para login
        import hashlib
        salt_login = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_login.encode('utf-8'), 100000)
        pwd_hash = dk.hex()
        
        # 3. Actualizar Nube
        print(">>> Actualizando Supabase (Usuario y Vault Access)...")
        supabase.table("users").update({
            "password_hash": pwd_hash,
            "salt": salt_login,
            "vault_salt": "\\x" + new_v_salt.hex(),
            "protected_key": "\\x" + protected_key.hex(),
            "active": True
        }).eq("id", user_id).execute()
        
        supabase.table("vault_access").upsert({
            "user_id": user_id,
            "vault_id": vault_id,
            "wrapped_master_key": protected_key.hex()
        }).execute()
        
        # 4. Limpieza Local Total
        print(">>> Purgando archivos locales antiguos...")
        data_dir = Path("data")
        if data_dir.exists():
            for f in data_dir.glob("*.db"):
                try: os.remove(f)
                except: pass
        
        print("\n" + "="*60)
        print("SISTEMA REPARADO EXITOSAMENTE.")
        print("Ahora puedes entrar con tu password y las llaves estarán LISTAS.")
        print("="*60)
        
    except Exception as e:
        print(f"Error fatal durante la reparación: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USO: python REPARACION_NUCLEAR.py TU_PASSWORD")
    else:
        nuclear_repair(sys.argv[1])
