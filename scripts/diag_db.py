import sqlite3
try:
    conn = sqlite3.connect('c:/PassGuardian_v2/data/vault_rodolfo.db')
    cur = conn.execute("SELECT username, salt, vault_salt, protected_key, wrapped_vault_key, user_id FROM users WHERE username = 'RODOLFO'")
    row = cur.fetchone()
    if row:
        columns = [d[0] for d in cur.description]
        data = dict(zip(columns, row))
        for k, v in data.items():
            if isinstance(v, bytes):
                print(f"{k}: Bytes (len={len(v)})")
            else:
                print(f"{k}: {v}")
    else:
        print("User RODOLFO not found")
except Exception as e:
    print(f"Error: {e}")
