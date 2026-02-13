"""
Verificar registros de RODOLFO en la DB de KIKI
"""
import sqlite3
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

db_path = r"C:\PassGuardian_v2\data\vault_kiki.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("REGISTROS DE RODOLFO EN LA DB DE KIKI")
print("=" * 80)

cursor.execute("SELECT id, service, username, owner_name, is_private FROM secrets WHERE UPPER(owner_name) = 'RODOLFO'")
records = cursor.fetchall()

if not records:
    print("\nNO HAY REGISTROS DE RODOLFO EN LA DB DE KIKI")
else:
    for r in records:
        print(f"\nID: {r[0]}")
        print(f"  Service: {r[1]}")
        print(f"  Username: {r[2]}")
        print(f"  Owner Name: {r[3]}")
        print(f"  Is Private: {r[4]}")

print("\n" + "=" * 80)
print("TODOS LOS REGISTROS:")
print("=" * 80)

cursor.execute("SELECT id, service, owner_name, is_private FROM secrets")
all_records = cursor.fetchall()

for r in all_records:
    print(f"ID {r[0]}: {r[1]} (Owner: {r[2]}, Private: {r[3]})")

conn.close()
