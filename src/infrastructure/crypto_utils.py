from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64

class CryptoUtils:
    @staticmethod
    def derive_key(master_password: str, salt: bytes = None) -> (bytes, bytes):
        if not salt:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000
        )
        key = kdf.derive(master_password.encode())
        return key, salt

    @staticmethod
    def encrypt(plaintext: str, key: bytes) -> (str, str):
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(ct).decode(), base64.b64encode(nonce).decode()

    @staticmethod
    def decrypt(ciphertext_b64: str, key: bytes, nonce_b64: str) -> str:
        aesgcm = AESGCM(key)
        ct = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)
        return aesgcm.decrypt(nonce, ct, None).decode()
