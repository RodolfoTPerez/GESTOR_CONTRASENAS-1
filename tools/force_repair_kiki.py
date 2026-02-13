
from supabase import create_client
import os
import sys
import base64

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager

def force_repair_kiki():
    print("--- REPARACIÓN DE EMERGENCIA: KIKI ---")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    sm = SecretsManager()
    um = UserManager(sm)
    
    # 1. Obtener perfil de KIKI desde la nube usando la lógica oficial
    cloud_profile = um.validate_user_access("KIKI")
    if not cloud_profile or not cloud_profile.get("exists"):
        print("❌ Error: KIKI no existe en Supabase")
        return
        
    print(f">>> Perfil encontrado en la nube. Protected Key: {len(cloud_profile.get('protected_key') or '')} chars")
    print(f">>> Wrapped Vault Key (Team): {'PRESENT' if cloud_profile.get('wrapped_vault_key') else 'MISSING'}")

    # 2. Sincronizar a base de datos local
    # Aseguramos que se escriba en vault_kiki.db
    um.sync_user_to_local("KIKI", cloud_profile)
    
    # 3. Verificación final
    import sqlite3
    conn = sqlite3.connect("data/vault_kiki.db")
    cur = conn.execute("SELECT username, length(protected_key), length(wrapped_vault_key) FROM users")
    row = cur.fetchone()
    print(f"--- Resultado Local (vault_kiki.db) ---")
    print(f"Usuario: {row[0]}")
    print(f"Protected Key Size: {row[1]} bytes")
    print(f"Wrapped Key Size: {row[2]} bytes")
    conn.close()

if __name__ == "__main__":
    force_repair_kiki()
