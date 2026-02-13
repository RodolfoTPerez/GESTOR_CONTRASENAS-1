
import sqlite3

def verify_indices():
    db_path = r"C:\PassGuardian_v2\data\vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA index_list(secrets)")
    indices = cursor.fetchall()
    print("Indices on 'secrets':")
    for idx in indices:
        print(idx)
        # Check details of the index
        name = idx[1]
        cursor.execute(f"PRAGMA index_info({name})")
        cols = cursor.fetchall()
        print(f"  Columns: {cols}")
    conn.close()

if __name__ == "__main__":
    verify_indices()
