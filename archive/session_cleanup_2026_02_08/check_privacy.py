
import sqlite3

def check_kiki_privacy():
    db_path = r"C:\PassGuardian_v2\data\vault_kiki.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"Checking privacy of 'PUMBA' in {db_path}...")
    cursor.execute("SELECT id, service, username, is_private FROM secrets WHERE service = 'PUMBA'")
    row = cursor.fetchone()
    if row:
        print(f"ID: {row[0]} | Service: {row[1]} | User: {row[2]} | IsPrivate: {row[3]}")
    else:
        print("Record not found.")
    conn.close()

if __name__ == "__main__":
    check_kiki_privacy()
