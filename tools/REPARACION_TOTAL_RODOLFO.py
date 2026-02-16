from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import sqlite3
import os
from pathlib import Path
import sys

# Asegurar que el path incluya la raíz del proyecto para importar Managers
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager

def reparacion_identidad():
    db_path = str(BASE_DIR) + "/data/vault_rodolfo.db"
    
    if not os.path.exists(db_path):
        print(f"Error: No se encuentra la base de datos en {db_path}")
        return

    print(">>> Iniciando Cirugía de Identidad para RODOLFO...")
    
    try:
        conn = sqlite3.connect(db_path)
        # 1. Limpiar datos corruptos de la tabla users
        conn.execute("DELETE FROM users WHERE username = 'RODOLFO'")
        conn.commit()
        print("[OK] Perfil local purgado.")
        conn.close()

        # 2. Generar nueva infraestructura de llaves limpia usando los managers reales
        um = UserManager()
        sm = SecretsManager()
        
        import getpass
        password = getpass.getpass("Ingrese contraseña para REPARACIÓN: ")
        v_salt = os.urandom(16)
        pwd_hash, salt = um.hash_password(password)
        
        # Generar llave maestra limpia
        master_key = os.urandom(32)
        # Envolverla correctamente
        protected_key = sm.wrap_key(master_key, password, v_salt)
        
        # 3. Insertar perfil fresco y limpio
        conn = sqlite3.connect(db_path)
        cols = "username, password_hash, salt, vault_salt, role, active, protected_key, vault_id"
        vals = ("RODOLFO", pwd_hash, salt, sqlite3.Binary(v_salt), "admin", 1, sqlite3.Binary(protected_key), "0637ae0d-7446-4c94-bc06-18c918ce596e")
        conn.execute(f"INSERT INTO users ({cols}) VALUES (?,?,?,?,?,?,?,?)", vals)
        conn.commit()
        conn.close()
        
        print("[OK] Identidad reconstruida localmente con llaves frescas.")
        print("\n>>> CRÍTICO: Las llaves ahora están en READY. Procede con el SQL en Supabase.")
        
    except Exception as e:
        print(f"Error durante la reparación: {e}")

if __name__ == "__main__":
    reparacion_identidad()
