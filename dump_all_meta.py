import sqlite3
from pathlib import Path

def dump_meta(db_name):
    db_path = Path(f"data/{db_name}")
    if not db_path.exists():
        print(f"File not found: {db_path}")
        return
    
    print(f"\n--- {db_name.upper()} META ---")
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT key, hex(value) as val_hex FROM meta")
        for row in cursor.fetchall():
            print(f"Key: {row['key']} | Value: {row['val_hex']}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_meta("vultrax.db")
    dump_meta("vault_rodolfo.db")
