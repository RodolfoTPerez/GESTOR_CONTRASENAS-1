import sqlite3
from pathlib import Path

def dump_full_key():
    conn = sqlite3.connect("data/vault_rodolfo.db")
    key = conn.execute("SELECT wrapped_vault_key FROM users WHERE username='RODOLFO'").fetchone()[0]
    conn.close()
    
    print(f"Full Key Hex: {key.hex()}")
    print(f"Nonce (12b): {key[:12].hex()}")
    print(f"EncData(32b): {key[12:44].hex()}")
    print(f"Tag   (16b): {key[44:].hex()}")

if __name__ == "__main__":
    dump_full_key()
