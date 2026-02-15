import sqlite3
import os

def check_global_db():
    data_dir = "c:\\PassGuardian_v2\\data"
    db_path = os.path.join(data_dir, "vultrax.db")
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    print(f"Checking DB: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("\n--- USERS ---")
    try:
        cur.execute("SELECT * FROM users")
        for r in cur.fetchall(): print(r)
    except: pass

    print("\n--- META ---")
    try:
        cur.execute("SELECT * FROM meta")
        for r in cur.fetchall():
            k, v = r
            print(f"{k}: {v}")
            if "2c0d890746fcba5dc25bb693ac950a8fe5906e717545479675d1197a3c4d5cc6" in str(v):
                print("!!!! FOUND HASH IN META !!!!")
    except: pass

    conn.close()

if __name__ == "__main__":
    check_global_db()
