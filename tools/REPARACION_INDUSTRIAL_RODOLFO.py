import os
import sys
import base64
import secrets
from pathlib import Path

# Configuración de rutas
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.crypto_engine import CryptoEngine

def reparacion_industrial(password="123456"): # <--- CAMBIA ESTO POR TU PASSWORD REAL
    print("\n" + "="*60)
    print("REPARACION INDUSTRIAL DE IDENTIDAD (RODOLFO)")
    print("="*60)
    
    sm = SecretsManager()
    um = UserManager(sm)
    username = "RODOLFO"
    
    print(f">>> Obteniendo perfil de la nube...")
    u_res = um.supabase.table("users").select("*").eq("username", username).execute()
    if not u_res.data:
        print("Error: No se encontró el usuario en la nube.")
        return
    
    user_data = u_res.data[0]
    user_id = user_data['id']
    vault_id = user_data['vault_id']
    
    # 1. Generar nueva infraestructura de llaves limpia
    print(">>> Generando nueva infraestructura de llaves...")
    v_salt = secrets.token_bytes(16)
    master_key = CryptoEngine.generate_vault_master_key()
    
    # 2. Envolver llaves con el nuevo salt y password
    print(">>> Envolviendo llaves...")
    protected_key = CryptoEngine.wrap_vault_key(master_key, password, v_salt)
    wrapped_vault = CryptoEngine.wrap_vault_key(master_key, password, v_salt)
    
    # 3. Subir a Supabase (Users y Vault Access)
    print(">>> Sincronizando con Supabase...")
    payload_user = {
        "vault_salt": base64.b64encode(v_salt).decode('ascii'),
        "protected_key": base64.b64encode(protected_key).decode('ascii')
    }
    um.supabase.table("users").update(payload_user).eq("id", user_id).execute()
    
    um.supabase.table("vault_access").upsert({
        "user_id": user_id,
        "vault_id": vault_id,
        "wrapped_master_key": wrapped_vault.hex()
    }).execute()
    
    # 4. Estabilizar Localmente
    print(">>> Limpiando bases de datos locales antiguas...")
    sm.close()
    for db in Path("data").glob("*.db"):
        try: os.remove(db)
        except: pass
        
    print("\n" + "="*60)
    print("EXITO: Tus llaves han sido reiniciadas y sincronizadas.")
    print("Todo está listo para que inicies sesión normal.")
    print("="*60)

if __name__ == "__main__":
    # Si quieres cambiar el password aquí, hazlo. Por defecto usa '123456'
    # o el que estuvieras usando.
    reparacion_industrial("123456") 
