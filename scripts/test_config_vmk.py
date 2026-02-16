import sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Config from test_vault_config.txt
TEST_VMK_HEX = "f2413536f7c023e479ea167ddb7fd5bced1eadca0dc74da092647acf7cb274db"
TEST_VMK = bytes.fromhex(TEST_VMK_HEX)
DB_PATH = "data/vault_rodolfo.db"

def test_config_vmk():
    print(f"--- Forensic Test: Config VMK ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Get one locked secret from Dani
    s = conn.execute("SELECT service, secret, nonce FROM secrets WHERE owner_name LIKE '%DANI%' LIMIT 1").fetchone()
    if not s:
        print("No locked Dani records found.")
        return
        
    enc_data = bytes(s['secret'])
    nonce = bytes(s['nonce'])
    
    try:
        decrypted = AESGCM(TEST_VMK).decrypt(nonce, enc_data, None).decode("utf-8")
        print(f"✅ SUCCESS! Decrypted '{s['service']}' with Config VMK!")
    except Exception as e:
        print(f"Failed with Config VMK: {e}")
        
    conn.close()

if __name__ == "__main__":
    test_config_vmk()
