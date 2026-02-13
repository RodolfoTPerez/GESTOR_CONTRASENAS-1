import os
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# AES-256-GCM simple helper
class SimpleAES:
    @staticmethod
    def derive_key(password: str, salt: bytes, iterations=100_000) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    @staticmethod
    def encrypt(plaintext: str, password: str) -> str:
        salt = os.urandom(16)
        key = SimpleAES.derive_key(password, salt)
        iv = os.urandom(12)
        encryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        ).encryptor()
        ct = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return b64encode(salt + iv + encryptor.tag + ct).decode()

    @staticmethod
    def decrypt(ciphertext_b64: str, password: str) -> str:
        raw = b64decode(ciphertext_b64)
        salt, iv, tag, ct = raw[:16], raw[16:28], raw[28:44], raw[44:]
        key = SimpleAES.derive_key(password, salt)
        decryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        ).decryptor()
        pt = decryptor.update(ct) + decryptor.finalize()
        return pt.decode()
