
import sqlite3
from pathlib import Path

def fix_vault_profiles():
    data_dir = Path(r"c:\PassGuardian_v2\data")
    global_db = data_dir / "passguardian.db"
    
    if not global_db.exists():
        print(f"No se encontró la DB global en {global_db}")
        return

    # Conectar a la DB global para obtener usuarios
    conn_g = sqlite3.connect(global_db)
    cur_g = conn_g.execute("SELECT * FROM users")
    users = cur_g.fetchall()
    conn_g.close()

    if not users:
        print("No hay usuarios en la DB global.")
        return

    for user_row in users:
        username = user_row[0] # assume index 0 is username
        vault_db = data_dir / f"vault_{username.lower()}.db"
        
        if vault_db.exists():
            print(f">>> Reparando perfil en {vault_db.name}...")
            conn_v = sqlite3.connect(vault_db)
            # Asegurar que la tabla existe
            conn_v.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT,
                    salt TEXT,
                    vault_salt BLOB,
                    role TEXT,
                    active BOOLEAN DEFAULT 1,
                    protected_key BLOB,
                    totp_secret BLOB
                )
            """)
            # Insertar o reemplazar el perfil (9 columnas: username, pwd_hash, salt, v_salt, role, active, p_key, totp, vault_id)
            placeholders = ",".join(["?"] * len(user_row))
            conn_v.execute(
                f"INSERT OR REPLACE INTO users VALUES ({placeholders})",
                user_row
            )
            conn_v.commit()
            conn_v.close()
            print(f"    OK: Perfil de {username} sincronizado localmente.")

if __name__ == "__main__":
    fix_vault_profiles()
