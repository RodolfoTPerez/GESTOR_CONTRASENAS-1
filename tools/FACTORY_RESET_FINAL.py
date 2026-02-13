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

def factory_reset():
    print("="*60)
    print("PROTOCOLO DE ESTERILIZACIÓN TOTAL (FACTORY RESET)")
    print("="*60)

    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json"
    }

    # 1. LIMPIEZA DE NUBE (SUPABASE)
    tablas = ["secrets", "vault_access", "invitations", "users", "vaults", "vault_groups", "security_audit"]
    
    print("\n[1/2] Limpiando tablas en Supabase...")
    for tabla in tablas:
        print(f"  - Purgando tabla '{tabla}'...")
        try:
            # Delete without filters is allowed in Supabase if RLS is off or if using Service Role Key
            # We use a filter that matches everything to be safe with PostgREST
            r = requests.delete(f"{URL}/rest/v1/{tabla}?id=neq.0", headers=headers)
            # If id column doesn't exist (like in some junction tables), try alternative
            if r.status_code == 400:
                 r = requests.delete(f"{URL}/rest/v1/{tabla}", headers=headers)
            
            if r.status_code in (200, 204):
                print(f"    [OK] Tabla {tabla} vaciada.")
            else:
                print(f"    [AVISO] {tabla}: Status {r.status_code}")
        except Exception as e:
            print(f"    [ERROR] No se pudo purgar {tabla}: {e}")

    # 2. LIMPIEZA LOCAL
    print("\n[2/2] Purgando archivos locales...")
    
    # Directorio data
    data_dir = Path(str(BASE_DIR) + "/data")
    if data_dir.exists():
        for f in data_dir.glob("*.db"):
            try:
                os.remove(f)
                print(f"  - Eliminado: {f.name}")
            except Exception as e:
                print(f"  - Error eliminando {f.name}: {e}")
                
    # Archivos sueltos en root (por si acaso)
    for f in Path(str(BASE_DIR) + "").glob("vault_*.db"):
        try:
            os.remove(f)
            print(f"  - Eliminado: {f.name}")
        except: pass
    
    # Archivo passguardian.db en root
    p_db = Path(str(BASE_DIR) + "/passguardian.db")
    if p_db.exists():
        try: os.remove(p_db); print("  - Eliminado: passguardian.db")
        except: pass

    print("\n" + "="*60)
    print("SISTEMA ESTERILIZADO EXITOSAMENTE")
    print("="*60)
    print("\nPRÓXIMOS PASOS:")
    print("1. Ejecuta 'python main.py'")
    print("2. El sistema detectará que no hay administrador.")
    print("3. Crea tu usuario RODOLFO nuevamente.")
    print("4. Todo será CIEN POR CIEN NUEVO y blindado.")
    print("="*60)

if __name__ == "__main__":
    factory_reset()
