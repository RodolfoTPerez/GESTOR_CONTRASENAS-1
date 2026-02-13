"""
Verificar esquema de la tabla secrets en SQLite
"""
import sqlite3
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db_path = r"C:\PassGuardian_v2\data\vault_kiki.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("ESQUEMA DE LA TABLA SECRETS")
print("=" * 80)

# Ver columnas
cursor.execute("PRAGMA table_info(secrets)")
columns = cursor.fetchall()

print("\nCOLUMNAS:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Ver algunos registros
print("\n" + "=" * 80)
print("PRIMEROS 3 REGISTROS:")
print("=" * 80)

cursor.execute("SELECT id, service, username, owner_name, is_private FROM secrets LIMIT 3")
records = cursor.fetchall()

for r in records:
    print(f"\nID: {r[0]}")
    print(f"  Service: {r[1]}")
    print(f"  Username: {r[2]}")
    print(f"  Owner Name: {r[3] if len(r) > 3 else 'N/A'}")
    print(f"  Is Private: {r[4] if len(r) > 4 else 'N/A'}")

conn.close()
