
import sqlite3

def check_rodolfo_pumba_privacy():
    db_path = r"C:\PassGuardian_v2\data\vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"Checking privacy of 'PUMBA' in {db_path}...")
    cursor.execute("SELECT id, service, username, owner_name, is_private FROM secrets WHERE service = 'PUMBA'")
    rows = cursor.fetchall()
    for r in rows:
        print(f"ID: {r[0]} | Service: {r[1]} | User: {r[2]} | Owner: {r[3]} | IsPrivate: {r[4]}")
    conn.close()

if __name__ == "__main__":
    check_rodolfo_pumba_privacy()
