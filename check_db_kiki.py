import sqlite3
import os
import sys

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_kiki_audit_full():
    data_dir = "c:\\PassGuardian_v2\\data"
    db_path = os.path.join(data_dir, "vault_kiki.db")
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    print(f"Checking DB: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("\n--- SECURITY_AUDIT TABLE (FULL) ---")
    try:
        cur.execute("SELECT * FROM security_audit WHERE synced = 0")
        cols = [d[0] for d in cur.description]
        print(cols)
        rows = cur.fetchall()
        for r in rows:
            # Handle each element safely
            safe_row = []
            for item in r:
                if isinstance(item, str):
                    safe_row.append(item.encode('utf-8', 'replace').decode('utf-8'))
                else:
                    safe_row.append(item)
            print(tuple(safe_row))
    except Exception as e:
        print(f"Error reading audit: {e}")

    conn.close()

if __name__ == "__main__":
    check_kiki_audit_full()
