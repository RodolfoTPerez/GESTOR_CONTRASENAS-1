import os
import shutil
from pathlib import Path

def nuke_all_local_dbs():
    print("--- ☢️  OPERACIÓN RESSET NUCLEAR (LOCAL) ☢️  ---")
    print("Este programa limpiará TODA la basura de tu PC para forzar una sincronización limpia de la nube.")
    
    # Lista de posibles ubicaciones de bases de datos encontradas en el sistema
    base_paths = [
        Path(r"c:\PassGuardian_v2"),
        Path(r"c:\PassGuardian_v2\data"),
        Path(r"c:\PassGuardian_v2\src\data")
    ]
    
    count = 0
    for p in base_paths:
        if not p.exists(): continue
        
        # Buscar todos los archivos .db en estas carpetas
        for db_file in p.glob("*.db"):
            try:
                backup_name = db_file.with_suffix(".db.bak")
                print(f"📦 Respaldando {db_file.name} -> {backup_name.name}")
                shutil.copy2(db_file, backup_name)
                
                print(f"🔥 Eliminando {db_file.name}...")
                db_file.unlink()
                count += 1
            except Exception as e:
                print(f"❌ No se pudo eliminar {db_file.name} (¿está abierto el PassGuardian?): {e}")

    # Limpiar logs
    log_file = Path(r"c:\PassGuardian_v2\app.log")
    if log_file.exists():
        try:
            log_file.unlink()
            print("📝 Logs limpiados.")
        except: pass

    print("-" * 40)
    if count > 0:
        print(f"✅ ÉXITO: Se limpiaron {count} bases de datos locales.")
        print("PASOS A SEGUIR:")
        print("1. Abre PassGuardian.")
        print("2. Loguéate con tu contraseña de siempre.")
        print("3. El sistema BAJARÁ TODO LIMPIO de la nube de forma automática.")
        print("4. Intenta cambiar tu Firma Maestra ahora.")
    else:
        print("⚠️ No se encontraron archivos .db para limpiar.")

if __name__ == "__main__":
    nuke_all_local_dbs()
