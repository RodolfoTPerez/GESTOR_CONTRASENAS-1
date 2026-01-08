import os
import base64
from cryptography.hazmat.primitives.kdf.argon2 import Argon2
from cryptography.hazmat.primitives.kdf.argon2 import Type as Argon2Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pyotp
from contextlib import contextmanager

# =========================
# CONFIGURACIÓN ARGON2
# =========================
ARGON2_MEMORY_COST = 64 * 1024  # KB -> 64 MB
ARGON2_ITERATIONS = 3
ARGON2_PARALLELISM = 2
ARGON2_SALT_LENGTH = 16
KEY_LENGTH = 32  # 256 bits

# =========================
# CLAVE MAESTRA
# =========================
def generate_salt():
    return os.urandom(ARGON2_SALT_LENGTH)

def derive_master_key(password: str, salt: bytes) -> bytes:
    """
    Deriva una clave segura desde la clave maestra usando Argon2id.
    """
    password_bytes = password.encode()
    kdf = Argon2(
        memory_cost=ARGON2_MEMORY_COST,
        time_cost=ARGON2_ITERATIONS,
        parallelism=ARGON2_PARALLELISM,
        length=KEY_LENGTH,
        salt=salt,
        type=Argon2Type.ID
    )
    key = kdf.derive(password_bytes)
    return key

# =========================
# CIFRADO / DESCIFRADO
# =========================
def encrypt_secret(key: bytes, plaintext: str) -> tuple[bytes, bytes]:
    """
    Cifra un secreto usando AES-256-GCM.
    Devuelve (ciphertext, nonce)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 12 bytes recomendado
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return ciphertext, nonce

def decrypt_secret(key: bytes, ciphertext: bytes, nonce: bytes) -> str:
    """
    Descifra un secreto usando AES-256-GCM.
    """
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()

# =========================
# CONTEXTO SEGURO PARA CLAVE
# =========================
@contextmanager
def temporary_master_key(password: str, salt: bytes):
    """
    Context manager para derivar temporalmente la clave maestra
    y garantizar limpieza al salir del bloque.
    """
    key = derive_master_key(password, salt)
    try:
        yield key
    finally:
        # sobrescribir key en memoria
        for i in range(len(key)):
            key[i] = 0

# =========================
# TOTP / 2FA
# =========================
def generate_totp_secret() -> str:
    """
    Genera un secreto Base32 para TOTP.
    """
    return pyotp.random_base32()

def get_totp_token(secret: str) -> str:
    """
    Obtiene el token TOTP actual.
    """
    totp = pyotp.TOTP(secret)
    return totp.now()

def verify_totp(secret: str, token: str) -> bool:
    """
    Verifica un token TOTP.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # ventana de 1 intervalo

