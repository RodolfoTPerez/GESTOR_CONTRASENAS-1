import sqlite3
from pathlib import Path

def get_rodolfo_id():
    conn = sqlite3.connect("data/vault_rodolfo.db")
    user = conn.execute("SELECT user_id, username FROM users WHERE username='RODOLFO'").fetchone()
    if user:
        print(f"RODOLFO Username: {user[1]}")
        print(f"RODOLFO UUID:     {user[0]}")
    else:
        print("RODOLFO not found.")
    conn.close()

if __name__ == "__main__":
    get_rodolfo_id()
