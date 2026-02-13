from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import shutil
from pathlib import Path
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY

def master_reset():
    print("="*60)
    print("🔥 INICIANDO MASTER RESET - PASSGUARDIAN SENIOR EDITION 🔥")
    print("="*60)

    # 1. LIMPIEZA LOCAL
    print("\n[1/2] Limpiando Bóvedas Locales...")
    data_dir = Path(str(BASE_DIR) + "/data")
    if data_dir.exists():
        for file in data_dir.glob("*.db"):
            try:
                os.remove(file)
                print(f"  ✅ Eliminado: {file.name}")
            except Exception as e:
                print(f"  ❌ Error eliminando {file.name}: {e}")
    else:
        print("  ℹ️ Directorio 'data' no encontrado. Nada que limpiar localmente.")

    # 2. LIMPIEZA NUBE (SUPABASE)
    print("\n[2/2] Limpiando Base de Datos en Supabase...")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # El orden es importante por las llaves foráneas
        tables = ["security_audit", "secrets", "vault_access", "invitations", "users"]
        
        for table in tables:
            try:
                if table == "users":
                    res = supabase.table(table).delete().neq("username", "NULL_RESET_VALUE").execute()
                elif table == "vault_access":
                    res = supabase.table(table).delete().neq("user_id", -1).execute()
                else:
                    res = supabase.table(table).delete().neq("id", -1).execute()
                print(f"  ✅ Tabla '{table}' limpiada exitosamente.")
            except Exception as te:
                print(f"  ❌ Error limpiando '{table}': {te}")
                
    except Exception as se:
        print(f"  ❌ Fallo crítico conectando a Supabase: {se}")

    print("\n" + "="*60)
    print("✨ RESET COMPLETADO EXITOSAMENTE ✨")
    print("Ahora puedes iniciar main.py y registrar al Administrador desde cero.")
    print("El nuevo motor de persistencia binaria protegerá tus nuevas llaves.")
    print("="*60)

if __name__ == "__main__":
    confirm = input("⚠️ ADVERTENCIA: Se borrarán TODOS los datos locales y en la nube. ¿Continuar? (si/no): ")
    if confirm.lower() == 'si':
        master_reset()
    else:
        print("Reset cancelado.")
