import os
import sys
import uuid
from supabase import create_client
from dotenv import load_dotenv

# Asegurar que el path incluya la raíz del proyecto para importar UserManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.user_manager import UserManager
from config.config import SUPABASE_URL, SUPABASE_KEY

def registrar_admin_forzado():
    load_dotenv()
    print("="*60)
    print("INICIANDO REGISTRO FORZADO DE ADMINISTRADOR EN CLOUD (v3)")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    um = UserManager()
    
    # DATOS DE ACCESO
    username = "RODOLFO"
    password = "RODOLFO" 
    instancia_nombre = "PASSGUARDIAN MAIN VAULT"
    # UUID para vincular todo
    v_uuid = "0637ae0d-7446-4c94-bc06-18c918ce596e"
    
    try:
        # 1. Configurar la Bóveda Maestra (UUID)
        print(f">>> Configurando instancia: {instancia_nombre}...")
        supabase.table("vaults").upsert({"id": v_uuid, "name": instancia_nombre}).execute()
        print("OK: Boveda creada.")
        
        # 2. Generar Hash compatible con la App
        pwd_hash, salt = um.hash_password(password)
        
        # 3. Registrar al Usuario Administrador vinculado al UUID
        payload = {
            "username": username.upper(),
            "role": "admin",
            "active": True,
            "password_hash": pwd_hash,
            "salt": salt,
            "vault_id": v_uuid # Usamos el UUID aquí para evitar error de sintaxis
        }
        
        print(f">>> Registrando Administrador {username} con Vault {v_uuid}...")
        res = supabase.table("users").insert(payload).execute()
        
        if res.data:
            print(f"OK: Administrador '{username}' registrado exitosamente.")
        
        print("\n" + "="*60)
        print("TERMINADO: Revisa tu panel de Supabase ahora.")
        print("="*60)
        
    except Exception as e:
        print(f"\nERROR CRITICO: {e}")

if __name__ == "__main__":
    registrar_admin_forzado()
