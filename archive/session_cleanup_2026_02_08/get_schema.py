
import sqlite3

def get_schema():
    db_path = r"C:\PassGuardian_v2\data\vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(secrets)")
    columns = cursor.fetchall()
    for c in columns:
        print(c)
    conn.close()

if __name__ == "__main__":
    get_schema()
