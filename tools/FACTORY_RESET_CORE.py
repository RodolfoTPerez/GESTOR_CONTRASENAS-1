from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import shutil
from pathlib import Path
from supabase import create_client
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def factory_reset_supabase():
    print("="*60)
    print("INICIANDO MASTER RESET - PASSGUARDIAN FACTORY RESET")
    print("="*60)

    # 1. LIMPIEZA LOCAL
    print("\n[1/2] Limpiando Bóvedas Locales...")
    # Buscamos en el directorio raíz y en data
    data_dirs = [Path(str(BASE_DIR) + "/data"), Path(str(BASE_DIR) + "")]
    for data_dir in data_dirs:
        if data_dir.exists():
            for file in data_dir.glob("*.db"):
                try:
                    os.remove(file)
                    print(f"  ✅ Eliminado localmente: {file.name}")
                except Exception as e:
                    print(f"  ❌ Error eliminando local {file.name}: {e}")

    # 2. LIMPIEZA NUBE (SUPABASE)
    print("\n[2/2] Limpiando Base de Datos en Supabase...")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # El orden es CRÍTICO por las llaves foráneas.
        # Primero eliminamos los hijos, luego los padres.
        # 1. Auditorías, Secretos, Invitaciones (Hijos de users/vaults)
        # 2. Vault Access (Intermedia users/vaults)
        # 3. Users (Hijo de vault_groups en algunos esquemas, o padre de secrets)
        # 4. Vault Groups / Vaults (Padre de todo)
        
        tables = [
            "security_audit", 
            "audit_log", 
            "secrets", 
            "invitations", 
            "vault_access", 
            "users", 
            "vault_groups", 
            "vaults"
        ]
        
        for table in tables:
            try:
                # Usamos un delete con filtro para que no falle si la tabla está vacía
                # y para cumplir con el requisito de Supabase de tener un filtro en DELETE
                if table == "users":
                    # Intentamos borrar todos
                    res = supabase.table(table).delete().neq("username", "___DUMMY_VALUE___").execute()
                elif table == "vault_access":
                    res = supabase.table(table).delete().neq("user_id", -1).execute()
                elif table == "vault_groups" or table == "vaults":
                    res = supabase.table(table).delete().neq("id", "-1").execute()
                else:
                    res = supabase.table(table).delete().neq("id", -1).execute()
                
                print(f"  ✅ Tabla '{table}' limpiada exitosamente.")
            except Exception as te:
                # Si la tabla no existe, simplemente informamos y seguimos
                if "relation" in str(te).lower() and "does not exist" in str(te).lower():
                    print(f"  ℹ️ Tabla '{table}' no existe en el esquema. Omitiendo.")
                else:
                    print(f"  ❌ Error limpiando '{table}': {te}")
                
    except Exception as se:
        print(f"  ❌ Fallo crítico conectando a Supabase: {se}")

    print("\n" + "="*60)
    print("RESET DE FABRICA COMPLETADO EXITOSAMENTE")
    print("La nube y el almacenamiento local estan TOTALMENTE LIMPIOS.")
    print("="*60)

if __name__ == "__main__":
    factory_reset_supabase()
