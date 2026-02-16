import sqlite3
import secrets
import sys
import time
from pathlib import Path

# Cryptography imports
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("Error: 'cryptography' library not found. Please install it with 'pip install cryptography'")
    sys.exit(1)

# Configuration
USERNAME = "RODOLFO"
USERNAME_UPPER = USERNAME.upper()
PROJECT_ROOT = Path(__file__).parent.parent
DB_FILE = PROJECT_ROOT / "data" / f"vault_{USERNAME.lower()}.db"

def run_repair():
    print("="*70)
    print("REGENERAR VAULT KEY - PASSGUARDIAN PRO")
    print("="*70)
    
    if not DB_FILE.exists():
        print(f"Error: Base de datos no encontrada en {DB_FILE}")
        return

    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Obtener Perfil
        print(f"Buscando perfil para {USERNAME_UPPER}...")
        user = cursor.execute("SELECT * FROM users WHERE UPPER(username) = ?", (USERNAME_UPPER,)).fetchone()
        
        if not user:
            print(f"Error: Usuario {USERNAME_UPPER} not found")
            return

        print(f"Perfil encontrado. Vault ID: {user['vault_id']}")
        
        # 2. Obtener Password (Interactivo)
        # Usamos input() para mayor visibilidad
        password = input(f"Ingrese password para {USERNAME_UPPER}: ").strip()
        if not password:
            print("Error: El password no puede estar vacio")
            return

        # 3. Manejar Salt
        vault_salt = user['vault_salt']
        if not vault_salt:
            print("Aviso: No se encontro vault_salt. Generando uno nuevo...")
            vault_salt = secrets.token_bytes(16)
        elif isinstance(vault_salt, str):
            try:
                vault_salt = bytes.fromhex(vault_salt)
            except:
                vault_salt = vault_salt.encode('utf-8')
        
        print(f"Usando salt: {vault_salt.hex()[:8]}...")

        # 4. Generar Nueva Llave (VMK)
        print("Generando nueva Vault Master Key de 256 bits...")
        new_vmk = secrets.token_bytes(32)
        
        # 5. Derivacion y Encriptacion
        print("Derivando KEK y empaquetando llave...")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=vault_salt,
            iterations=100000,
            backend=default_backend()
        )
        kek = kdf.derive(password.encode('utf-8'))
        
        nonce = secrets.token_bytes(12)
        aes_gcm = AESGCM(kek)
        wrapped_key = nonce + aes_gcm.encrypt(nonce, new_vmk, None)
        
        # 6. Actualizacion en BD
        print("Guardando cambios en la base de datos...")
        
        cursor.execute("""
            UPDATE users 
            SET wrapped_vault_key = ?, vault_salt = ? 
            WHERE UPPER(username) = ?
        """, (sqlite3.Binary(wrapped_key), sqlite3.Binary(vault_salt), USERNAME_UPPER))
        
        cursor.execute("""
            INSERT OR REPLACE INTO vault_access 
            (vault_id, wrapped_master_key, access_level, updated_at, synced) 
            VALUES (?, ?, ?, ?, ?)
        """, (user['vault_id'], sqlite3.Binary(wrapped_key), 'admin', int(time.time()), 0))
        
        conn.commit()
        print("\nREGENERACION EXITOSA!")
        print(f"La llave para {USERNAME_UPPER} ha sido reparada localmente.")
        print("La aplicacion subira esta nueva llave a la nube en tu proximo login.")
        print("="*70)

    except Exception as e:
        print(f"Error durante repair: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_repair()
