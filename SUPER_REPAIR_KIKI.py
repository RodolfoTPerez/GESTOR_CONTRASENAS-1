
import os
import base64
import sqlite3
import getpass
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.user_manager import UserManager
from src.infrastructure.crypto_engine import CryptoEngine

def super_repair():
    print("=== PASSGUARDIAN: PROTOCOLO DE REPARACION NUCLEAR ===")
    admin_pass = getpass.getpass("Ingrese su FIRMA MAESTRA (RODOLFO) para autorizar: ")
    
    sm = SecretsManager()
    um = UserManager(sm)
    
    # 1. Recuperar identidad de Rodolfo
    print("[1/4] Recuperando llaves de Rodolfo...")
    rodolfo_profile = sm.get_local_user_profile("RODOLFO")
    if not rodolfo_profile:
        print("ERROR: No se encontró perfil local de RODOLFO.")
        return

    try:
        # Derivar KEK para abrir la bóveda de Rodolfo
        v_salt = rodolfo_profile.get("vault_salt")
        kek = sm.security.derive_keke(admin_pass, v_salt)
        
        # Obtener la Master Key real
        w_v_key = rodolfo_profile.get("wrapped_vault_key")
        if not w_v_key:
            # Intentar desde vault_access
            va = sm.users.get_vault_access(rodolfo_profile.get("vault_id"))
            w_v_key = va.get("wrapped_master_key") if va else None
            
        if not w_v_key:
            print("ERROR: El administrador no tiene llaves de bóveda accesibles.")
            return
            
        master_key = sm.security.unwrap_key(w_v_key, admin_pass, v_salt)
        print(f"OK: Llave Maestra recuperada ({len(master_key)} bytes).")
        
    except Exception as e:
        print(f"ERROR de Autorización: {e}")
        return

    # 2. Preparar para KIKI
    print("[2/4] Preparando identidad para KIKI...")
    target = "KIKI"
    new_kiki_pass = input(f"Ingrese la NUEVA contraseña para {target}: ")
    
    kiki_v_salt = os.urandom(16)
    kiki_personal_key = os.urandom(32)
    kiki_protected_key = sm.security.wrap_key(kiki_personal_key, new_kiki_pass, kiki_v_salt)
    kiki_vault_key_wrapped = sm.security.wrap_key(master_key, new_kiki_pass, kiki_v_salt)
    
    # 3. Inyectar en la Nube
    print("[3/4] Inyectando en Supabase...")
    kiki_cloud = um.validate_user_access(target)
    if not kiki_cloud or not kiki_cloud.get("exists"):
        print("ERROR: KIKI no existe en la nube.")
        return
    
    kiki_uid = kiki_cloud['id']
    kiki_vid = kiki_cloud['vault_id']
    
    # Actualizar Perfil
    success, msg = um.update_user_password(
        target, new_kiki_pass,
        new_protected_key=base64.b64encode(kiki_protected_key).decode('ascii'),
        new_vault_salt=base64.b64encode(kiki_v_salt).decode('ascii')
    )
    
    if success:
        # INYECCION FORZADA EN vault_access
        print(f"Actualizando permisos de bóveda {kiki_vid} para {target}...")
        um.update_bulk_vault_access(kiki_uid, [(kiki_vid, kiki_vault_key_wrapped.hex())])
        print("??? EXITO: Permisos inyectados correctamente.")
    else:
        print(f"FALLO al actualizar perfil: {msg}")

    # 4. Limpieza
    print("[4/4] Finalizando...")
    print("\nREPARACION COMPLETADA. Pide a KIKI que inicie sesión ahora.")

if __name__ == "__main__":
    super_repair()
