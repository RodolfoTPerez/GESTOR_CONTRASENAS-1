from supabase import create_client
import uuid
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.secrets_manager import SecretsManager

def fix_vault():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    sm = SecretsManager()
    
    username = "RODOLFO"
    # 1. Generar nuevo Vault ID
    new_v_id = str(uuid.uuid4())
    instance_name = sm.get_meta("instance_name") or "SYSTEM SECURITY AI"
    
    print(f">>> Reparando Bóveda para {username}...")
    print(f">>> Nuevo Vault ID: {new_v_id}")
    print(f">>> Nombre: {instance_name}")
    
    try:
        # 2. Crear entrada en la tabla 'vaults'
        supabase.table("vaults").insert({"id": new_v_id, "name": instance_name}).execute()
        print(">>> Tabla 'vaults' actualizada.")
        
        # 3. Vincular usuario a esa bóveda
        supabase.table("users").update({"vault_id": new_v_id}).eq("username", username).execute()
        print(">>> Usuario vinculado a la bóveda en Supabase.")
        
        # 4. Actualizar localmente (Meta y Perfil)
        # Guardamos en meta para futuras referencias rápidas
        sm.set_meta("vault_id", new_v_id)
        
        # Actualizar perfil del usuario local
        profile = sm.get_local_user_profile(username)
        if profile:
             sm.save_local_user_profile(
                 username, 
                 profile["password_hash"], 
                 profile["salt"], 
                 profile["vault_salt"], 
                 profile["role"], 
                 profile.get("protected_key"), 
                 profile.get("totp_secret"), 
                 new_v_id,
                 profile.get("wrapped_vault_key")
             )
        
        print(">>> Configuración local actualizada.")
        print("\n¡REPARACIÓN COMPLETADA! Ahora el nombre aparecerá en Supabase.")
        
    except Exception as e:
        print(f"Error durante la reparación: {e}")

if __name__ == "__main__":
    fix_vault()
