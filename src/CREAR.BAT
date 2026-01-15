(echo import json)>  src\infrastructure\secrets_manager.py
echo import sqlite3>>src\infrastructure\secrets_manager.py
echo import os>>src\infrastructure\secrets_manager.py
echo from cryptography.hazmat.primitives.ciphers.aead import AESGCM>>src\infrastructure\secrets_manager.py
echo.>>src\infrastructure\secrets_manager.py
echo class SecretsManager:>>src\infrastructure\secrets_manager.py
echo     def __init__(self, master_password):>>src\infrastructure\secrets_manager.py
echo         self.master_key = master_password.encode()>>src\infrastructure\secrets_manager.py
echo         from pathlib import Path>>src\infrastructure\secrets_manager.py
echo         DB_PATH = Path(__file__).resolve().parent.parent.parent / "passguardian.db">>src\infrastructure\secrets_manager.py
echo         self.conn = sqlite3.connect(DB_PATH)>>src\infrastructure\secrets_manager.py
echo         self.create_table()>>src\infrastructure\secrets_manager.py
echo.>>src\infrastructure\secrets_manager.py

Copy
(echo     def create_table(self):>>src\infrastructure\secrets_manager.py
echo         self.conn.execute("""CREATE TABLE IF NOT EXISTS secrets ^(id INTEGER PRIMARY KEY, service TEXT, username TEXT, secret BLOB, nonce BLOB^)""")>>src\infrastructure\secrets_manager.py
echo         self.conn.commit()>>src\infrastructure\secrets_manager.py
echo.>>src\infrastructure\secrets_manager.py
(usamos ^ para escapar los paréntesis en cmd).

Copy
(echo     def add_secret(self, service, username, secret_plain):>>src\infrastructure\secrets_manager.py
echo         import os,numpy>>src\infrastructure\secrets_manager.py
echo         nonce = os.urandom(12)>>src\infrastructure\secrets_manager.py
echo         aes = AESGCM(self.master_key.ljust(32, b'\0'))>>src\infrastructure\secrets_manager.py
echo         secret_encrypted = aes.encrypt(nonce, secret_plain.encode(), None)>>src\infrastructure\secrets_manager.py
echo         self.conn.execute("INSERT INTO secrets (service, username, secret, nonce) VALUES (?,?,?,?)", (service, username, secret_encrypted, nonce))>>src\infrastructure\secrets_manager.py
echo         self.conn.commit()>>src\infrastructure\secrets_manager.py
echo.>>src\infrastructure\secrets_manager.py
Y terminar:
Copy
(echo     def get_all(self):>>src\infrastructure\secrets_manager.py
echo         cursor = self.conn.execute("SELECT service, username, secret, nonce FROM secrets")>>src\infrastructure\secrets_manager.py
echo         results = []>>src\infrastructure\secrets_manager.py
echo         for row in cursor:>>src\infrastructure\secrets_manager.py
echo             aes = AESGCM(self.master_key.ljust(32, b'\0'))>>src\infrastructure\secrets_manager.py
echo             secret_plain = aes.decrypt(row[3], row[2], None).decode()>>src\infrastructure\secrets_manager.py
echo             results.append({"service": row[0], "username": row[1], "secret": secret_plain})>>src\infrastructure\secrets_manager.py
echo         return results>>src\infrastructure\secrets_manager.py
