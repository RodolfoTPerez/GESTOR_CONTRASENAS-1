import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.argon2 import Argon2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pyotp
from datetime import datetime

# ===============================
# CONFIGURACIÓN Y CONSTANTES
# ===============================
AES_KEY_LENGTH = 32  # 256 bits
NONCE_LENGTH = 12    # recomendado para AES-GCM
PBKDF2_ITERATIONS = 100_000
SALT_LENGTH = 16

# ===============================
# DERIVACIÓN DE CLAVE MAESTRA
# ===============================
def derive_master_key(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """
    Deriva la clave maestra usando PBKDF2 (seguro) o Argon2.
    Retorna (key, salt) si se genera uno nuevo.
    """
    if salt is None:
        salt = os.urandom(SALT_LENGTH)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password.encode())
    return key, salt

# ===============================
# CIFRADO Y DESCIFRADO AES-GCM
# ===============================
def encrypt_secret(key: bytes, plaintext: str) -> tuple[bytes, bytes]:
    """
    Cifra el texto plano usando AES-256-GCM.
    Retorna (ciphertext, nonce)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LENGTH)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return ciphertext, nonce

def decrypt_secret(key: bytes, ciphertext: bytes, nonce: bytes) -> str:
    """
    Descifra un ciphertext usando AES-256-GCM.
    """
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()

# ===============================
# COMPLEJIDAD DE CONTRASEÑA
# ===============================
def password_strength(password: str) -> tuple[int, str]:
    """
    Evalúa la fuerza de la contraseña y retorna (score 0-100, categoría)
    """
    score = 0
    length = len(password)

    if length >= 8:
        score += 20
    if any(c.islower() for c in password):
        score += 20
    if any(c.isupper() for c in password):
        score += 20
    if any(c.isdigit() for c in password):
        score += 20
    if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~" for c in password):
        score += 20

    if score >= 80:
        category = "Fuerte"
    elif score >= 50:
        category = "Media"
    else:
        category = "Débil"

    return score, category

# ===============================
# TOTP (2FA)
# ===============================
def generate_totp_secret() -> str:
    """
    Genera un secreto base32 para TOTP.
    """
    return pyotp.random_base32()

def get_totp_token(secret: str) -> str:
    """
    Obtiene token TOTP actual (válido 30s).
    """
    totp = pyotp.TOTP(secret)
    return totp.now()

def verify_totp(secret: str, token: str) -> bool:
    """
    Verifica si el token TOTP es válido.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token)

# ===============================
# EJEMPLOS DE USO
# ===============================
if __name__ == "__main__":
    # Derivar clave maestra
    password = "MiClaveMaestra123!"
    key, salt = derive_master_key(password)
    print(f"Clave maestra derivada: {base64.b64encode(key).decode()}")
    print(f"Salt usado: {base64.b64encode(salt).decode()}")

    # Cifrar y descifrar
    secret_text = "contraseña_super_secreta"
    ciphertext, nonce = encrypt_secret(key, secret_text)
    print(f"Ciphertext: {base64.b64encode(ciphertext).decode()}")
    print(f"Nonce: {base64.b64encode(nonce).decode()}")

    decrypted = decrypt_secret(key, ciphertext, nonce)
    print(f"Descifrado: {decrypted}")

    # Evaluar contraseña
    score, category = password_strength(secret_text)
    print(f"Fuerza: {score}% ({category})")

    # TOTP
    totp_secret = generate_totp_secret()
    print(f"Secreto TOTP: {totp_secret}")
    print(f"Token actual: {get_totp_token(totp_secret)}")
    print(f"Verificación: {verify_totp(totp_secret, get_totp_token(totp_secret))}")

