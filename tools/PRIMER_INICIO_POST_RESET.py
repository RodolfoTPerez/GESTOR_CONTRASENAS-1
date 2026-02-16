import os
import sys
import base64
import secrets
import hashlib
from supabase import create_client
from dotenv import load_dotenv

# Asegurar que el path incluya la raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.user_manager import UserManager
from src.infrastructure.crypto_engine import CryptoEngine
from config.config import SUPABASE_URL, SUPABASE_KEY

# ID Fijo para la Bóveda Maestra (Estándar de PassGuardian v2)
MASTER_VAULT_UUID = "0637ae0d-7446-4c94-bc06-18c918ce596e"

def primer_inicio():
    print("="*80)
    print("🚀 PROCESO DE PRIMER INICIO (FACTORY RESET RECOVERY) - PassGuardian v2")
    print("="*80)
    print("Este script configura los cimientos de la base de datos tras un TRUNCATE.\n")

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    um = UserManager()

    # 1. Configuración de Bóvedas
    print("-" * 50)
    print("1. CONFIGURANDO INFRAESTRUCTURA DE BÓVEDAS")
    print("-" * 50)
    try:
        # Bóveda Principal (Donde viven los secretos compartidos)
        sb.table("vaults").upsert({
            "id": MASTER_VAULT_UUID, 
            "name": "PASSGUARDIAN MAIN VAULT"
        }).execute()
        print(f"   [OK] Bóveda Maestra vinculada: {MASTER_VAULT_UUID}")

        # Grupo IA (Para lógica de Guardian AI)
        ai_key = secrets.token_hex(32)
        sb.table("vault_groups").upsert({
            "id": 1,
            "vault_name": "AI SECURITY SYSTEM",
            "vault_master_key": f"\\x{ai_key}", # Formato bytea
            "max_users": 5
        }).execute()
        print("   [OK] Sistema de Seguridad IA inicializado.")
    except Exception as e:
        print(f"   [Error] Configuración de infraestructura: {e}")

    # 2. Registro del Administrador Maestro
    print("\n" + "-" * 50)
    print("2. REGISTRO DE ADMINISTRADOR MAESTRO")
    print("-" * 50)
    
    username = "RODOLFO"
    import getpass
    password = getpass.getpass("Ingrese contraseña de PRIMER INICIO: ")
    
    try:
        print(f"   Generando llaves E2EE para '{username}'...")
        # Generar Sal de Bóveda (Inmutable)
        v_salt_bytes = secrets.token_bytes(16)
        
        # Generar Hash de Contraseña
        pwd_hash, salt = um.hash_password(password)
        
        # Generar Llave Maestra original del sistema (32 bytes)
        new_master_key = secrets.token_bytes(32)
        
        # Envolver la llave (Key Wrapping) para persistencia en nube
        protected_key_bytes = CryptoEngine.wrap_vault_key(new_master_key, password, v_salt_bytes)
        
        payload = {
            "username": username.upper(),
            "role": "admin",
            "active": True,
            "vault_id": MASTER_VAULT_UUID,
            "password_hash": pwd_hash,
            "salt": salt,
            "vault_salt": base64.b64encode(v_salt_bytes).decode('ascii'),
            "protected_key": base64.b64encode(protected_key_bytes).decode('ascii')
        }
        
        print(f"   Registrando en la nube...")
        res = sb.table("users").upsert(payload).execute()
        
        if res.data:
            admin_id = res.data[0]['id']
            print(f"   [OK] Administrador Registrado (ID: {admin_id})")
            
            # 3. Vincular Acceso a Bóveda (Tabla puente)
            print("   Vinculando acceso oficial a la bóveda...")
            sb.table("vault_access").upsert({
                "user_id": admin_id,
                "vault_id": MASTER_VAULT_UUID,
                "wrapped_master_key": protected_key_bytes.hex()
            }).execute()
            print("   [OK] Acceso a Bóveda Maestra concedido.")
            
            # 4. Estabilización Local (SQLite)
            print("\n" + "-" * 50)
            print("3. ESTABILIZACIÓN DEL ENTORNO LOCAL")
            print("-" * 50)
            print(f"   Creando base de datos local vault_{username.lower()}.db...")
            um.sync_user_to_local(username, res.data[0])
            print("   [OK] Caché local sincronizado.")
            
            print("\n" + "="*80)
            print("✨ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
            print(f"USUARIO: {username}")
            print(f"PASS:    {password}")
            print("-" * 80)
            print("PASO SIGUIENTE: Abre la aplicación e inicia sesión normalmente.")
            print("="*80)
            
        else:
            print("   [Error] La nube no devolvió confirmación de registro.")

    except Exception as e:
        print(f"\n❌ [ERROR CRÍTICO DURING SETUP]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    primer_inicio()
