"""
FACTORY RESET FINAL - PassGuardian
Elimina TODA la data de Supabase y local
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from pathlib import Path
import sys

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("FACTORY RESET FINAL - PASSGUARDIAN")
print("=" * 80)

# Conectar a Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Estrategia: Obtener todos los registros y eliminarlos uno por uno

# 1. Limpiar tabla secrets
print("\n[1/6] Limpiando tabla 'secrets'...")
try:
    records = supabase.table("secrets").select("id").execute()
    if records.data:
        for record in records.data:
            supabase.table("secrets").delete().eq("id", record['id']).execute()
        print(f"   OK - {len(records.data)} registros eliminados")
    else:
        print(f"   INFO - Tabla ya estaba vacia")
except Exception as e:
    print(f"   WARN - Error: {e}")

# 2. Limpiar tabla security_audit
print("\n[2/6] Limpiando tabla 'security_audit'...")
try:
    records = supabase.table("security_audit").select("id").execute()
    if records.data:
        for record in records.data:
            supabase.table("security_audit").delete().eq("id", record['id']).execute()
        print(f"   OK - {len(records.data)} registros eliminados")
    else:
        print(f"   INFO - Tabla ya estaba vacia")
except Exception as e:
    print(f"   WARN - Error: {e}")

# 3. Limpiar tabla invitations
print("\n[3/6] Limpiando tabla 'invitations'...")
try:
    records = supabase.table("invitations").select("id").execute()
    if records.data:
        for record in records.data:
            supabase.table("invitations").delete().eq("id", record['id']).execute()
        print(f"   OK - {len(records.data)} registros eliminados")
    else:
        print(f"   INFO - Tabla ya estaba vacia")
except Exception as e:
    print(f"   WARN - Error: {e}")

# 4. Limpiar tabla vault_access
print("\n[4/6] Limpiando tabla 'vault_access'...")
try:
    records = supabase.table("vault_access").select("id").execute()
    if records.data:
        for record in records.data:
            supabase.table("vault_access").delete().eq("id", record['id']).execute()
        print(f"   OK - {len(records.data)} registros eliminados")
    else:
        print(f"   INFO - Tabla ya estaba vacia")
except Exception as e:
    print(f"   WARN - Error: {e}")

# 5. Limpiar tabla users
print("\n[5/6] Limpiando tabla 'users'...")
try:
    records = supabase.table("users").select("id").execute()
    if records.data:
        for record in records.data:
            supabase.table("users").delete().eq("id", record['id']).execute()
        print(f"   OK - {len(records.data)} registros eliminados")
    else:
        print(f"   INFO - Tabla ya estaba vacia")
except Exception as e:
    print(f"   WARN - Error: {e}")

# 6. Eliminar todas las bases de datos locales
print("\n[6/6] Eliminando bases de datos locales...")
base_dir = Path(__file__).resolve().parent
data_dir = base_dir / "data"

if data_dir.exists():
    db_files = list(data_dir.glob("*.db"))
    if db_files:
        for db_file in db_files:
            try:
                db_file.unlink()
                print(f"   OK - Eliminado: {db_file.name}")
            except Exception as e:
                print(f"   WARN - Error eliminando {db_file.name}: {e}")
    else:
        print(f"   INFO - No hay archivos .db para eliminar")
else:
    print(f"   INFO - Directorio 'data' no existe")

print("\n" + "=" * 80)
print("FACTORY RESET COMPLETADO")
print("=" * 80)
print("\nEl sistema ha sido restaurado a su estado inicial.")
print("Ejecuta: python main.py")
print("=" * 80)
