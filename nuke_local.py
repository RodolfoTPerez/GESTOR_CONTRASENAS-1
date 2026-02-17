import os
import shutil
import sqlite3
from pathlib import Path

def nuke_all_local_state():
    print("--- ☢️  OPERACIÓN LIMPIEZA TOTAL (ULTRA AGGRESSIVE) ☢️  ---")
    print("Objetivo: Eliminar cualquier base de datos local que esté bloqueando la sincronización de la nube.")
    
    # 1. Identificar rutas críticas
    root = Path(".").resolve()
    data_dir = root / "data"
    src_data = root / "src" / "data"
    
    all_targets = [root, data_dir, src_data]
    
    count = 0
    for folder in all_targets:
        if not folder.exists(): continue
        print(f"Scanning: {folder}")
        # Buscar .db, .db-journal, .db-wal y .bak
        for pattern in ["*.db", "*.db-journal", "*.db-wal"]:
            for f in folder.glob(pattern):
                try:
                    # No borrar los backups viejos, pero sí los archivos activos
                    print(f"📦 Creando respaldo final: {f.name}.nuclear.bak")
                    shutil.copy2(f, f.with_name(f.name + ".nuclear.bak"))
                    
                    print(f"🔥 Eliminando: {f.name}")
                    f.unlink()
                    count += 1
                except Exception as e:
                    print(f"❌ ERROR: No se pudo eliminar {f.name}. ¡CIERRA EL PASSGUARDIAN! ({e})")

    # 2. Limpiar logs para que no nos confundan
    log_file = root / "app.log"
    if log_file.exists():
        try:
            log_file.unlink()
            print("📝 Logs reseteados.")
        except: pass

    print("-" * 50)
    if count > 0:
        print(f"✅ ÉXITO: Se eliminaron {count} archivos de estado local.")
        print("\nPASOS CRÍTICOS:")
        print("1. Abre el programa PassGuardian.")
        print("2. Entra con tu contraseña.")
        print("3. EL SISTEMA AHORA BAJARÁ TODO LIMPIO DE LA NUBE (ya quité el bloqueo de conflicto).")
        print("4. Cambia tu Firma Maestra ahora.")
    else:
        print("⚠️ No se encontraron archivos para limpiar. Si el problema persiste, asegúrate de haber CERRADO el app antes de correr esto.")

if __name__ == "__main__":
    nuke_all_local_state()
