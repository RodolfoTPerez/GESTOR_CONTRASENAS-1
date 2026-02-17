
import sqlite3
import os
from pathlib import Path

data_dir = Path("c:/PassGuardian_v2/data")
for user_db in ["kiki", "rodolfo"]:
    db_path = data_dir / f"vault_{user_db}.db"
    if not db_path.exists():
        print(f"\nSkipping {user_db}: File not found")
        continue

    print(f"\n=== INSPECTING {user_db.upper()} DB ===")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

print("--- Local Profile in vault_kiki.db ---")
cursor.execute("SELECT username, user_id FROM users")
for row in cursor.fetchall():
    print(f"User: {row[0]}, ID: {row[1]}")

print("\n--- Pending Audit Logs with IDs ---")
cursor.execute("SELECT id, action, user_id, synced FROM security_audit WHERE synced = 0")
for row in cursor.fetchall():
    print(f"LOG ID: {row[0]}, Action: {row[1]}, UserID: {row[2]}, Synced: {row[3]}")

conn.close()
