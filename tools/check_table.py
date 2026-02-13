"""
Ver estructura de la tabla users
"""
import sqlite3
from pathlib import Path

db_path = Path(r"C:\PassGuardian_v2\data\passguardian.db")
conn = sqlite3.connect(db_path)

cursor = conn.execute("PRAGMA table_info(users)")
print("Columnas de la tabla users:")
for row in cursor:
    print(f"  - {row[1]} ({row[2]})")

conn.close()
