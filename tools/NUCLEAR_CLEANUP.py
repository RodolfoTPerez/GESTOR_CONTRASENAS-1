from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(str(BASE_DIR) + "/.env")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def clean_table(table):
    print(f"  - Limpiando tabla '{table}'...")
    try:
        # Intentar borrar con filtro de "no es nulo" en alguna columna común
        # Probamos con id para usuarios/vaults o owner_name para secrets
        filters = ["id=neq.0", "id=gt.0", "username=neq.EMPTY", "owner_name=neq.EMPTY", "code=neq.EMPTY", "vault_id=neq.EMPTY"]
        
        success = False
        for f in filters:
            r = requests.delete(f"{URL}/rest/v1/{table}?{f}", headers=headers)
            if r.status_code in (200, 204):
                print(f"    [OK] Purgada con filtro {f}.")
                success = True
                break
        
        if not success:
            # Plan B: Intentar sin filtros si está permitido
            r = requests.delete(f"{URL}/rest/v1/{table}", headers=headers)
            if r.status_code in (200, 204):
                print(f"    [OK] Purgada sin filtros.")
            else:
                print(f"    [AVISO] No se pudo purgar {table} (Status {r.status_code})")
                
    except Exception as e:
        print(f"    [ERROR] Error en {table}: {e}")

def nuclear_reset():
    print("="*60)
    print("RESETEO NUCLEAR (ESTILIZACIÓN TOTAL)")
    print("="*60)

    # 1. Nube
    tablas = ["secrets", "vault_access", "invitations", "security_audit", "users", "vaults", "vault_groups"]
    print("\n[1/2] Purgando Nube...")
    for t in tablas:
        clean_table(t)

    # 2. Local
    print("\n[2/2] Purgando Local...")
    data_dir = Path(str(BASE_DIR) + "/data")
    if data_dir.exists():
        for f in data_dir.glob("*.db"):
            try:
                os.remove(f)
                print(f"  - Eliminado: {f.name}")
            except Exception as e:
                print(f"  - No se pudo eliminar {f.name}: {e}")

    print("\n" + "="*60)
    print("TODO LIMPIO. SISTEMA EN ESTADO 'VIRGEN'.")
    print("="*60)

if __name__ == "__main__":
    nuclear_reset()
