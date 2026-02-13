from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import sqlite3
import os
import sys
import base64
from pathlib import Path

def hard_reset_rodolfo():
    db_user = str(BASE_DIR) + "/data/vault_rodolfo.db"
    db_meta = str(BASE_DIR) + "/data/passguardian.db"
    
    print(">>> Iniciando Reparación Multi-Base de Datos...")

    try:
        # 1. Reparar PERFIL en vault_rodolfo.db
        conn_u = sqlite3.connect(db_user)
        conn_u.execute("DELETE FROM users WHERE UPPER(username) = 'RODOLFO'")
        
        password = "RODOLFO"
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        salt_pwd = os.urandom(16)
        salt_vault = os.urandom(16)
        
        # Derivación manual de llaves para evitar fallos de clase
        kdf_h = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt_pwd, iterations=100000)
        pwd_hash = base64.b64encode(kdf_h.derive(password.encode())).decode()
        
        master_key = os.urandom(32)
        kdf_k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt_vault, iterations=100000)
        kek = kdf_k.derive(password.encode())
        
        nonce = os.urandom(12)
        protected_key = nonce + AESGCM(kek).encrypt(nonce, master_key, None)
        
        vault_id = "0637ae0d-7446-4c94-bc06-18c918ce596e"
        
        cols = "username, password_hash, salt, vault_salt, role, active, protected_key, vault_id, totp_secret"
        vals = ("RODOLFO", pwd_hash, salt_pwd, salt_vault, "admin", 1, sqlite3.Binary(protected_key), vault_id, "JBSWY3DPEHPK3PXP")
        conn_u.execute(f"INSERT INTO users ({cols}) VALUES (?,?,?,?,?,?,?,?,?)", vals)
        conn_u.commit()
        conn_u.close()
        print("[OK] vault_rodolfo.db REPARADO.")

        # 2. Reparar ACCESOS en passguardian.db
        if os.path.exists(db_meta):
            conn_m = sqlite3.connect(db_meta)
            # Asegurarnos de que existe la tabla
            conn_m.execute("CREATE TABLE IF NOT EXISTS vault_access (vault_id TEXT, owner_name TEXT, role TEXT)")
            conn_m.execute("DELETE FROM vault_access WHERE UPPER(owner_name) = 'RODOLFO'")
            conn_m.execute("INSERT INTO vault_access (vault_id, owner_name, role) VALUES (?,?,?)", (vault_id, "RODOLFO", "admin"))
            conn_m.commit()
            conn_m.close()
            print("[OK] passguardian.db REPARADO.")
        
        print("\n>>> IDENTIDAD LOCAL SELLADA. Las llaves ahora deben decir READY.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    hard_reset_rodolfo()
