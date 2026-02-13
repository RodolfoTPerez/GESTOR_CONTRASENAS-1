
import os
import sys
import base64
import hashlib
import sqlite3
from supabase import create_client

# Configuración de rutas e importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.user_manager import UserManager
from src.infrastructure.crypto_engine import CryptoEngine

def anchor_rodolfo_keys():
    print("=== PROTOCOLO DE ENCLAVAMIENTO DE LLAVES: RODOLFO ===")
    
    # 1. Solicitar credenciales para derivar la KEK
    password = input("Ingrese la contraseña actual de RODOLFO para autorizar el enclavamiento: ")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    sm = SecretsManager()
    um = UserManager(sm)
    
    # 2. Obtener perfil de Rodolfo desde la nube
    res = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
    if not res.data:
        print("❌ Error: RODOLFO no encontrado en la nube.")
        return
    
    cloud_profile = res.data[0]
    v_id = cloud_profile.get("vault_id")
    
    # 3. Derivar o Generar Salt y Llave Maestra
    # Para consistencia, usamos el salt de la nube si existe, si no generamos uno nuevo.
    v_salt_b64 = cloud_profile.get("vault_salt")
    if v_salt_b64:
        v_salt = base64.b64decode(v_salt_b64)
    else:
        v_salt = os.urandom(16)
        v_salt_b64 = base64.b64encode(v_salt).decode('ascii')
    
    # GENERAMOS UNA NUEVA LLAVE MAESTRA COMPARTIBLE (VAULT KEY)
    # Esta será la llave que KIKI y RODOLFO compartirán para ver registros públicos.
    master_key = CryptoEngine.generate_vault_master_key()
    
    # 4. Envolver la llave (Wrapping)
    # Protegemos la llave maestra con la contraseña de Rodolfo
    protected_key = CryptoEngine.wrap_vault_key(master_key, password, v_salt)
    protected_key_b64 = base64.b64encode(protected_key).decode('ascii')
    
    print(f">>> Generada nueva Master Key Core.")
    print(f">>> Envolviendo llave para RODOLFO (SVK)...")

    # 5. ACTUALIZAR NUBE (Supabase)
    update_payload = {
        "vault_salt": v_salt_b64,
        "protected_key": protected_key_b64
    }
    
    try:
        supabase.table("users").update(update_payload).eq("username", "RODOLFO").execute()
        print("✅ Perfil de RODOLFO actualizado en Supabase.")
        
        # 6. VINCULAR EN VAULT_ACCESS
        # Esto permite que el sistema de invitaciones y otros procesos encuentren la llave
        access_payload = {
            "wrapped_master_key": protected_key.hex()
        }
        try:
            # Primero intentamos actualizar el registro existente
            res_upd = supabase.table("vault_access").update(access_payload).eq("user_id", cloud_profile['id']).eq("vault_id", v_id).execute()
            if not res_upd.data:
                # Si no existe, lo insertamos
                access_payload.update({"user_id": cloud_profile['id'], "vault_id": v_id})
                supabase.table("vault_access").insert(access_payload).execute()
                print("✅ Acceso a Bóveda (Vault Access) creado.")
            else:
                print("✅ Acceso a Bóveda (Vault Access) actualizado.")
        except Exception as e:
            print(f"⚠️ Nota: Error manejando vault_access: {e}")

        # 7. SINCRONIZAR LOCALMENTE
        um.sync_user_to_local("RODOLFO", {**cloud_profile, **update_payload})
        print("✅ Base de datos local (vault_rodolfo.db) sincronizada.")
        
        print("\n" + "="*50)
        print("¡LLAVE ENCLAVADA EXITOSAMENTE!")
        print("Ahora los registros de RODOLFO serán legibles para KIKI.")
        print("IMPORTANTE: Los registros creados ANTES de este paso podrían seguir bloqueados")
        print("ya que fueron creados con una llave temporal inexistente.")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    anchor_rodolfo_keys()
