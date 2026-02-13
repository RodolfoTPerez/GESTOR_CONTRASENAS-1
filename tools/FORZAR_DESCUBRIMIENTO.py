from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR) + "/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def descubrimiento_masivo():
    # Diccionario de tablas y listas de columnas probables
    plan = {
        "secrets": ["id", "owner_id", "vault_id", "title", "name", "username", "password", "url", "notes", "encrypted_data", "is_public", "created_at", "updated_at"],
        "users": ["id", "username", "password_hash", "salt", "vault_salt", "role", "active", "protected_key", "totp_secret", "vault_id", "created_at"],
        "vaults": ["id", "name", "created_at"]
    }
    
    for tabla, cols in plan.items():
        print(f"\n[TABLA: {tabla}]")
        detectadas = []
        for c in cols:
            try:
                supabase.table(tabla).select(c).limit(0).execute()
                detectadas.append(c)
            except Exception as e:
                err = str(e)
                if "42703" not in err:
                    detectadas.append(f"{c}")
        print(f"  Confirmadas: {', '.join(detectadas)}")

if __name__ == "__main__":
    descubrimiento_masivo()
