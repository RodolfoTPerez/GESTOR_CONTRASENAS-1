
import sqlite3
conn = sqlite3.connect('data/vault_rodolfo.db')
print(conn.execute("SELECT sql FROM sqlite_master WHERE name='security_audit'").fetchone()[0])
conn.close()
