from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import sqlite3
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.infrastructure.user_manager import UserManager
from config.config import SUPABASE_URL, SUPABASE_KEY

def main():
    um = UserManager()
    data_dir = Path(str(BASE_DIR) + "/data")
    users = ["RODOLFO", "KIKI", "KAREN", "DANIEL"]
    
    print(">>> INICIANDO RESET PARA SHOWCASE DE BARRA DE PROGRESO...")

    # 1. Limpiar Nube (Supabase) para estos usuarios
    print(">>> Limpiando registros en la nube...")
    for user in users:
        try:
            # Eliminamos los secretos en Supabase para que el sistema local los vea como "nuevos" a subir
            res = um.supabase.table("secrets").delete().eq("owner_name", user).execute()
            print(f"  [Cloud] Registros eliminados para {user}.")
        except Exception as e:
            print(f"  [Error Cloud] No se pudo limpiar nube para {user}: {e}")

    # 2. Resetear Local (SQLite)
    print(">>> Marcando registros locales como 'No Sincronizados'...")
    for user in users:
        db_path = data_dir / f"vault_{user.lower()}.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # Marcamos todo como pendiente de subir (synced=0)
                # También nos aseguramos de que no tengan cloud_id para que el sync los trate como inserciones nuevas
                cursor.execute("UPDATE secrets SET synced = 0, cloud_id = NULL")
                count = conn.total_changes
                conn.commit()
                conn.close()
                print(f"  [Local] {count} registros preparados en {db_path.name}")
            except Exception as e:
                print(f"  [Error Local] Fallo en {db_path.name}: {e}")
        else:
            print(f"  [Aviso] No se encontró DB local para {user}")

    print("\n>>> ¡LISTO! El escenario está preparado.")
    print(">>> Cuando inicies sesión con cualquiera de estos usuarios y des click en SINCRONIZAR,")
    print(">>> verás la BARRA DE PROGRESO subiendo los 100+ registros uno por uno.")

if __name__ == "__main__":
    main()
