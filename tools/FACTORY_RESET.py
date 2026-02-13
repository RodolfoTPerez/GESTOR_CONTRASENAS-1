"""
FACTORY RESET COMPLETO - PassGuardian
Elimina TODA la data de Supabase y local, dejando el sistema como recien instalado
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import os
from pathlib import Path
import sys

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("FACTORY RESET COMPLETO - PASSGUARDIAN")
print("=" * 80)

print("\nEsta accion eliminara:")
print("  - Todos los usuarios de Supabase")
print("  - Todos los secretos de Supabase")
print("  - Todos los registros de auditoria de Supabase")
print("  - Todas las invitaciones de Supabase")
print("  - Todos los archivos de base de datos local")

print("\n[ADVERTENCIA] ESTA ACCION ES IRREVERSIBLE")
print("\nPresiona ENTER para continuar o CTRL+C para cancelar...")
input()
confirmacion = input("\nEscribe 'RESET' para confirmar: ")

if confirmacion != "RESET":
    print("\n[CANCELADO] Factory reset cancelado")
    exit(0)

print("\n[INICIANDO FACTORY RESET...]")

# Conectar a Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Limpiar tabla secrets
print("\n[1/6] Limpiando tabla 'secrets'...")
try:
    result = supabase.table("secrets").delete().neq("id", 0).execute()
    print(f"   ✓ Tabla 'secrets' limpiada")
except Exception as e:
    print(f"   ⚠️  Error limpiando 'secrets': {e}")

# 2. Limpiar tabla security_audit
print("\n[2/6] Limpiando tabla 'security_audit'...")
try:
    result = supabase.table("security_audit").delete().neq("id", 0).execute()
    print(f"   ✓ Tabla 'security_audit' limpiada")
except Exception as e:
    print(f"   ⚠️  Error limpiando 'security_audit': {e}")

# 3. Limpiar tabla invitations
print("\n[3/6] Limpiando tabla 'invitations'...")
try:
    result = supabase.table("invitations").delete().neq("id", 0).execute()
    print(f"   ✓ Tabla 'invitations' limpiada")
except Exception as e:
    print(f"   ⚠️  Error limpiando 'invitations': {e}")

# 4. Limpiar tabla vault_access
print("\n[4/6] Limpiando tabla 'vault_access'...")
try:
    result = supabase.table("vault_access").delete().neq("id", 0).execute()
    print(f"   ✓ Tabla 'vault_access' limpiada")
except Exception as e:
    print(f"   ⚠️  Error limpiando 'vault_access': {e}")

# 5. Limpiar tabla users
print("\n[5/6] Limpiando tabla 'users'...")
try:
    result = supabase.table("users").delete().neq("id", 0).execute()
    print(f"   ✓ Tabla 'users' limpiada")
except Exception as e:
    print(f"   ⚠️  Error limpiando 'users': {e}")

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
                print(f"   ✓ Eliminado: {db_file.name}")
            except Exception as e:
                print(f"   ⚠️  Error eliminando {db_file.name}: {e}")
    else:
        print(f"   ℹ️  No hay archivos .db para eliminar")
else:
    print(f"   ℹ️  Directorio 'data' no existe")

print("\n" + "=" * 80)
print("FACTORY RESET COMPLETADO")
print("=" * 80)
print("\nEl sistema ha sido restaurado a su estado inicial.")
print("Puedes ejecutar 'python main.py' para crear un nuevo usuario administrador.")
print("\n" + "=" * 80)
