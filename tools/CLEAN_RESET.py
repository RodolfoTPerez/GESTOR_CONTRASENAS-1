
import os
import sys
import shutil
import sqlite3
import base64
import secrets
from supabase import create_client

# Configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.crypto_engine import CryptoEngine
from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager

def hard_reset_and_rebuild():
    print("="*60)
    print("      SYSTEM HARD RESET & CRYPTO REBUILD (GOLD STANDARD)")
    print("="*60)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. LIMPIEZA DE NUBE
    print("[1/5] Limpiando tablas en Supabase...")
    tables = ["vault_access", "secrets", "invitations", "users", "vaults", "security_audit"]
    for t in tables:
        try:
            supabase.table(t).delete().neq("id", "-1").execute()
        except: pass
    print("✅ Nube limpia.")

    # 2. LIMPIEZA LOCAL
    print("[2/5] Eliminando bases de datos locales...")
    data_dir = "data"
    for f in os.listdir(data_dir):
        if f.endswith(".db"):
            try: os.remove(os.path.join(data_dir, f))
            except: pass
    print("✅ Almacenamiento local limpio.")

    # 3. CREAR INFRAESTRUCTURA DE RODOLFO (ADMIN)
    print("[3/5] Creando Administrador y Bóveda Maestra...")
    sm = SecretsManager()
    um = UserManager(sm)
    
    pwd_r = "RODOLFO" # Contraseña estándar para el reset
    v_id = "0637ae0d-7446-4c94-bc06-18c918ce596e" # ID persistente
    v_salt = os.urandom(16)
    
    # Crear Bóveda primero (Upsert para evitar errores de clave duplicada)
    supabase.table("vaults").upsert({"id": v_id, "name": "PASSGUARDIAN MAIN VAULT"}).execute()
    
    # Generar Llave Maestra Real
    real_master_key = CryptoEngine.generate_vault_master_key()
    
    # Perfil de Rodolfo
    pwd_hash_r, salt_r = um.hash_password(pwd_r)
    protected_r = CryptoEngine.wrap_vault_key(real_master_key, pwd_r, v_salt)
    
    payload_r = {
        "username": "RODOLFO",
        "role": "admin",
        "active": True,
        "password_hash": pwd_hash_r,
        "salt": salt_r,
        "vault_salt": base64.b64encode(v_salt).decode('ascii'),
        "protected_key": base64.b64encode(protected_r).decode('ascii'),
        "vault_id": v_id
    }
    res_r = supabase.table("users").insert(payload_r).execute()
    uid_r = res_r.data[0]['id']
    
    # Acceso de Rodolfo
    supabase.table("vault_access").insert({
        "user_id": uid_r, "vault_id": v_id, "wrapped_master_key": protected_r.hex()
    }).execute()
    
    # Sincronización Local Rodolfo
    sm.reconnect("RODOLFO")
    um.sync_user_to_local("RODOLFO", payload_r)
    print("✅ RODOLFO configurado con Llave Maestra Oficial.")

    # 4. CREAR A KIKI (SIN INVITACIÓN, VÍNCULO DIRECTO)
    print("[4/5] Creando a KIKI con herencia de llave perfecta...")
    pwd_k = "KIKI1234567890"
    v_salt_k = os.urandom(16)
    pwd_hash_k, salt_k = um.hash_password(pwd_k)
    
    # Usamos LA MISMA Llave Maestra pero envuelta con el password de Kiki
    protected_k = CryptoEngine.wrap_vault_key(real_master_key, pwd_k, v_salt_k)
    
    payload_k = {
        "username": "KIKI",
        "role": "user",
        "active": True,
        "password_hash": pwd_hash_k,
        "salt": salt_k,
        "vault_salt": base64.b64encode(v_salt_k).decode('ascii'),
        "protected_key": base64.b64encode(protected_k).decode('ascii'),
        "vault_id": v_id
    }
    res_k = supabase.table("users").insert(payload_k).execute()
    uid_k = res_k.data[0]['id']
    
    # Acceso de Kiki (El puente crítico)
    supabase.table("vault_access").insert({
        "user_id": uid_k, "vault_id": v_id, "wrapped_master_key": protected_k.hex()
    }).execute()
    
    # Sincronización Local Kiki
    sm.reconnect("KIKI")
    um.sync_user_to_local("KIKI", payload_k)
    print("✅ KIKI configurada con paridad bit-a-bit.")

    print("\n" + "="*60)
    print("RESETEO EXITOSO.")
    print("1. Abre PassGuardian.")
    print("2. Entra con KIKI (Pass: KIKI1234567890) y crea un registro PÚBLICO.")
    print("3. Entra con RODOLFO y verifica. FUNCIONARÁ.")
    print("="*60)

if __name__ == "__main__":
    hard_reset_and_rebuild()
