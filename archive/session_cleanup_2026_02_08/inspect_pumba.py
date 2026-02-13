
import sqlite3
import os

def inspect_pumba_details():
    db_path = r"C:\PassGuardian_v2\data\vault_rodolfo.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"Inspecting 'PUMBA' in {db_path}...")
        cursor.execute("SELECT id, service, username, created_at, updated_at, synced, cloud_id FROM secrets WHERE service = 'PUMBA'")
        rows = cursor.fetchall()
        for r in rows:
            print(f"ID: {r[0]} | Service: {r[1]} | User: {r[2]} | Created: {r[3]} | Updated: {r[4]} | Synced: {r[5]} | CloudID: {r[6]}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_pumba_details()
