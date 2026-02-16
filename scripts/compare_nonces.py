import sqlite3
from pathlib import Path

def compare_nonces():
    conn_r = sqlite3.connect("data/vault_rodolfo.db")
    rodolfo_key = conn_r.execute("SELECT wrapped_vault_key FROM users WHERE username='RODOLFO'").fetchone()[0]
    conn_r.close()
    
    conn_d = sqlite3.connect("data/vault_dani.db")
    dani_key = conn_d.execute("SELECT wrapped_vault_key FROM users WHERE username='DANI'").fetchone()[0]
    conn_d.close()
    
    print(f"Rodolfo Nonce: {rodolfo_key[:12].hex()}")
    print(f"Dani Nonce:    {dani_key[:12].hex()}")
    
    if rodolfo_key[:12] == dani_key[:12]:
        print("MATCH! The nonces are IDENTICAL.")
    else:
        print("DIFFERENT nonces.")

if __name__ == "__main__":
    compare_nonces()
