import sqlite3
import os

db_path = r"c:\PassGuardian_v2\data\passguardian.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    print("Users found:", users)
    conn.close()
else:
    print("DB not found at", db_path)
