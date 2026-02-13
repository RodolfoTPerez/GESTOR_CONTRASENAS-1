
import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Configuración de entorno
sys.path.insert(0, str(Path.cwd()))
load_dotenv()

# Mock de SecretsManager para probar SyncManager aislado
class MockSecretsManager:
    def __init__(self):
        self.current_user = "RODOLFO"
        self.current_user_id = None # Se llenará si la nube lo devuelve
        self.current_vault_id = "test-vault-id"
        self.conn = self
        
    def execute(self, query, params=()):
        # Mock de DB connection para evitar errores de SQL
        return self
        
    def commit(self):
        pass
        
    def fetchone(self):
        return None
        
    def get_all_encrypted(self, only_mine=False):
        return []

    def mark_as_synced(self, id, status):
        print(f"   [MockDB] Marcado como synced: {id}")

# Importar SyncManager
try:
    from src.infrastructure.sync_manager import SyncManager
    print("  Modulo SyncManager importado correctamente.")
except ImportError as e:
    print(f"  Error importando SyncManager: {e}")
    sys.exit(1)

def test_sync_connectivity():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("  Faltan credenciales en .env")
        return

    print(f"\n--- Probando SyncManager con URL: {url} ---")
    
    sm = MockSecretsManager()
    sync = SyncManager(sm, url, key)
    
    # 1. Prueba de Internet
    print("\n1. Verificando Conexion a Internet...")
    has_net = sync.check_internet()
    print(f"   Resultado: {'  Conectado' if has_net else '  Sin conexion'}")
    
    if not has_net:
        print("   Abortando pruebas dependientes de red.")
        return

    # 2. Prueba de Conexion a Supabase (Healthcheck)
    print("\n2. Verificando Acceso a Supabase (RLS Headers)...")
    try:
        ok = sync.check_supabase()
        print(f"   Resultado: {'  Acceso OK' if ok else '  Fallo de Acceso (Posible 401/403)'}")
    except Exception as e:
        print(f"   Excepcion: {e}")

    # 3. Prueba de Sesiones Activas (Widget de UI)
    print("\n3. Obteniendo Sesiones Activas (Para Widget UI)...")
    try:
        sessions = sync.get_active_sessions()
        print(f"   Sesiones encontradas: {len(sessions)}")
        for s in sessions:
            print(f"    - {s.get('device_name')} ({s.get('username')})")
    except Exception as e:
        print(f"   Error obteniendo sesiones: {e}")

    # 4. Prueba de Revocación (Kill Switch)
    print("\n4. Verificando Estado de Revocacion...")
    is_revoked = sync.check_revocation_status()
    print(f"   Estatus: {'  REVOCADO' if is_revoked else '  ACTIVO'}")

if __name__ == "__main__":
    test_sync_connectivity()
