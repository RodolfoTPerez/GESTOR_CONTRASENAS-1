
import sqlite3
import datetime

def inspect_pumba_final():
    db_path = r"C:\PassGuardian_v2\data\vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"Detailed inspection of 'PUMBA' in {db_path}...")
    cursor.execute("SELECT id, service, username, updated_at, owner_name, cloud_id FROM secrets WHERE service = 'PUMBA'")
    rows = cursor.fetchall()
    for r in rows:
        dt = datetime.datetime.fromtimestamp(r[3]) if r[3] else "N/A"
        print(f"ID: {r[0]} | Service: {r[1]} | User: {r[2]} | Updated: {dt} | Owner: {r[4]} | CloudID: {r[5]}")
    conn.close()

if __name__ == "__main__":
    inspect_pumba_final()
