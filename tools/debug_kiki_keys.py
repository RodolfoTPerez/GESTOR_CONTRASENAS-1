
import sqlite3
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_kek(password, salt, iterations=100_000):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)

def test_kiki_keys():
    # KIKI's data from common knowledge or previously retrieved
    # password is 'kiki' (assumed from context or common dev practice here)
    import getpass
    password = getpass.getpass("Ingrese contraseña (KIKI): ")
    
    conn = sqlite3.connect('data/vault_kiki.db')
    conn.row_factory = sqlite3.Row
    prof = conn.execute("SELECT * FROM users WHERE username='KIKI'").fetchone()
    conn.close()
    
    if not prof:
        print("KIKI profile not found")
        return

    salt = prof['vault_salt']
    pk_raw = prof['protected_key']
    wvk_raw = prof['wrapped_vault_key']
    
    print(f"Salt length: {len(salt)}")
    print(f"PK length: {len(pk_raw)}")
    print(f"WVK length: {len(wvk_raw)}")
    
    # Try common passwords
    for pwd in ["KIKI", "kiki", "123456"]:
        print(f"\nTesting password: {pwd}")
        kek = derive_kek(pwd, salt)
        
        try:
            # Try decrypt PK
            dec_pk = AESGCM(kek).decrypt(pk_raw[:12], pk_raw[12:], None)
            print(f"  [SUCCESS] Decrypted Personal Key with '{pwd}'")
            print(f"  Key start: {dec_pk[:4].hex()}")
        except Exception as e:
            print(f"  [FAIL] Could not decrypt PK with '{pwd}': {e}")

        try:
            # Try decrypt WVK
            dec_wvk = AESGCM(kek).decrypt(wvk_raw[:12], wvk_raw[12:], None)
            print(f"  [SUCCESS] Decrypted Vault Key with '{pwd}'")
            print(f"  Key start: {dec_wvk[:4].hex()}")
        except Exception as e:
            print(f"  [FAIL] Could not decrypt WVK with '{pwd}': {e}")

if __name__ == "__main__":
    test_kiki_keys()
