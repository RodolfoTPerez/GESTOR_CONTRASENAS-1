# -*- coding: utf-8 -*-
"""
CryptoEngine - Gestor Central de Criptografía para PassGuardian
================================================================

Responsabilidades:
- Generar llaves maestras para bóvedas
- Wrap/Unwrap de vault_master_key con password de usuario
- Cálculo de checksums para validación
- Operaciones criptográficas centralizadas

Autor: PassGuardian Team
Fecha: 2026-01-22
"""

import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import logging
import time
from functools import wraps
from src.infrastructure.security.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# [NEW] Global RateLimiter instance
auth_limiter = RateLimiter(max_attempts=5, window_seconds=60)

def rate_limit(max_attempts=5, window=60):
    """
    Decorador para prevenir ataques de fuerza bruta/timing.
    Crea un RateLimiter dedicado para esta función respetando sus parámetros.
    """
    # [SENIOR FIX] Cada función decorada tiene su propia instancia de límites
    limiter = RateLimiter(max_attempts=max_attempts, window_seconds=window)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Lógica Senior para Identificación de Llave:
            # 1. Si es un método, el primer arg es 'self'. Lo saltamos.
            relevant_args = args[1:] if args and hasattr(args[0], '__dict__') else args
            
            key_val = "global"
            if relevant_args:
                first = relevant_args[0]
                if isinstance(first, (bytes, bytearray)):
                    key_val = hashlib.sha256(first).hexdigest()[:12]
                else:
                    key_val = str(first).strip().lower()
            
            key = f"{func.__name__}_{key_val}"
            
            if limiter.is_blocked(key):
                remaining = limiter.get_remaining_seconds(key)
                logger.warning(f"Rate limit exceeded for {key}. Blocked for {remaining}s")
                raise ValueError(f"Demasiados intentos. Por favor espere {remaining} segundos.")
            
            try:
                result = func(*args, **kwargs)
                if result is True:
                    limiter.reset(key)
                return result
            except Exception as e:
                # Solo registramos intentos fallidos si son errores de valor o lógica (auth fail)
                limiter.record_attempt(key)
                raise e
        return wrapper
    return decorator

def reset_rate_limits():
    """Limpia el historial de intentos."""
    auth_limiter.attempts.clear()


class CryptoEngine:
    """
    Motor criptográfico centralizado para operaciones de Key Wrapping.
    Utiliza AESGCM (AES-256-GCM) para mantener compatibilidad con el sistema actual.
    """
    
    # Constantes criptográficas
    KEY_SIZE = 32  # 256 bits para AES-256
    NONCE_SIZE = 12  # Recomendado para AES-GCM
    DEFAULT_ITERATIONS = 100_000  # PBKDF2 iterations (OWASP Standard)

    @staticmethod
    def hash_user_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """
        Genera un hash seguro para la contraseña del usuario usando PBKDF2-HMAC-SHA256.
        Implementación centralizada y profesional alineada con el estándar de referencia.
        
        Args:
            password: Password en texto plano
            salt: Salt binario opcional (mínimo 16 bytes). Si es None, se genera uno.
            
        Returns:
            tuple: (hash_hex, salt_bytes)
        """
        if salt is None:
            salt = os.urandom(16)
        
        if not isinstance(salt, (bytes, bytearray)):
            raise TypeError(f"Salt must be bytes for centralized crypto, got {type(salt)}")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=CryptoEngine.DEFAULT_ITERATIONS,
            backend=default_backend()
        )
        
        dk = kdf.derive(password.encode('utf-8'))
        return dk.hex(), salt

    @staticmethod
    def verify_user_password(password: str, salt: bytes, stored_hash: str) -> bool:
        """
        Verifica una contraseña contra un hash almacenado.
        
        Args:
            password: Password ingresada por el usuario
            salt: Salt binario recuperado de la DB
            stored_hash: Hash hexadecimal recuperado de la DB
            
        Returns:
            bool: True si coincide, False en caso contrario
        """
        if not salt or not stored_hash:
            return False
            
        # Asegurar que el salt sea bytes (sqlite3.Binary -> bytes)
        if not isinstance(salt, (bytes, bytearray)) and hasattr(salt, '__bytes__'):
            salt = bytes(salt)
            
        calculated_hash, _ = CryptoEngine.hash_user_password(password, salt)
        return calculated_hash == stored_hash
    
    @staticmethod
    def generate_vault_master_key() -> bytes:
        """
        Genera una llave maestra aleatoria para una nueva bóveda.
        
        Returns:
            bytes: Llave AES-256 (32 bytes) criptográficamente segura
            
        Example:
            vault_key = CryptoEngine.generate_vault_master_key()
            # vault_key = b'\\x8a\\x12...' (32 bytes aleatorios)
        """
        return os.urandom(CryptoEngine.KEY_SIZE)
    
    @staticmethod
    def derive_kek_from_password(password: str, salt: bytes, iterations: int = DEFAULT_ITERATIONS) -> bytes:
        """
        Deriva una Key Encryption Key (KEK) desde una password usando PBKDF2.
        
        Args:
            password: Password del usuario en texto plano
            salt: Salt único del usuario (debe ser el mismo al wrap/unwrap)
            iterations: Número de iteraciones PBKDF2 (default: 100,000)
            
        Returns:
            bytes: KEK de 32 bytes derivada de la password
            
        Security Note:
            - El salt debe ser único por usuario
            - El mismo (password + salt + iterations) siempre produce la misma KEK
            - Nunca almacenar la KEK, solo derivarla cuando se necesita
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        if not isinstance(salt, bytes):
            raise TypeError("Salt must be bytes")
        if len(salt) < 16:
            raise ValueError("Salt must be at least 16 bytes")
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=CryptoEngine.KEY_SIZE,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode("utf-8"))
    
    @staticmethod
    def wrap_vault_key(vault_master_key: bytes, user_password: str, user_salt: bytes) -> bytes:
        """
        Encripta (wrap) la vault_master_key usando la password del usuario.
        
        Este es el corazón del Key Wrapping. La vault_master_key se encripta
        con una KEK derivada de la password del usuario, permitiendo que cada
        usuario guarde su propia copia encriptada de la llav compartida.
        
        Args:
            vault_master_key: Llave maestra de la bóveda (32 bytes)
            user_password: Password del usuario en texto plano
            user_salt: Salt único del usuario
            
        Returns:
            bytes: vault_master_key encriptada (nonce + ciphertext)
                  Formato: [12 bytes nonce][44 bytes ciphertext + tag]
                  Total: 56 bytes
                  
        Example:
            vault_key = generate_vault_master_key()  # 32 bytes
            wrapped = wrap_vault_key(vault_key, "user_password", user_salt)
            # wrapped = b'\\x3a\\x1f...\\x9b' (56 bytes: 12 nonce + 44 encrypted)
            
        Security Flow:
            1. user_password + user_salt → KEK (via PBKDF2)
            2. vault_master_key + KEK → wrapped_key (via AES-GCM)
            3. wrapped_key se almacena en vault_access table
        """
        if not isinstance(vault_master_key, bytes):
            raise TypeError("vault_master_key must be bytes")
        if len(vault_master_key) != CryptoEngine.KEY_SIZE:
            raise ValueError(f"vault_master_key must be exactly {CryptoEngine.KEY_SIZE} bytes")
            
        # Derivar KEK desde password del usuario
        # Revertido a 100,000 iteraciones para mantener compatibilidad
        kek = CryptoEngine.derive_kek_from_password(user_password, user_salt, 100000)
        
        # Generar nonce aleatorio
        nonce = os.urandom(CryptoEngine.NONCE_SIZE)
        
        # Encriptar vault_master_key con KEK
        aes_gcm = AESGCM(kek)
        ciphertext = aes_gcm.encrypt(nonce, vault_master_key, None)
        
        # Retornar nonce + ciphertext
        return nonce + ciphertext
    
    @staticmethod
    @rate_limit(max_attempts=20, window=30)
    def unwrap_vault_key(wrapped_key: bytes, user_password: str, user_salt: bytes) -> bytes:
        """
        Desencripta (unwrap) la vault_master_key usando la password del usuario.
        [ULTRA RECOVERY] Soporta múltiples recuentos de iteraciones (1k, 10k, 100k y 600k).
        """
        if not isinstance(wrapped_key, bytes):
            raise TypeError("wrapped_key must be bytes")
        if len(wrapped_key) < CryptoEngine.NONCE_SIZE + CryptoEngine.KEY_SIZE:
            raise ValueError("wrapped_key is too short")

        nonce = wrapped_key[:CryptoEngine.NONCE_SIZE]
        ciphertext = wrapped_key[CryptoEngine.NONCE_SIZE:]
        
        # Probar recuentos de iteraciones comunes (Standard, Ultra, Legacy y Forensic)
        for iter_count in [100000, 600000, 10000, 1000]:
            try:
                kek = CryptoEngine.derive_kek_from_password(user_password, user_salt, iterations=iter_count)
                aes_gcm = AESGCM(kek)
                return aes_gcm.decrypt(nonce, ciphertext, None)
            except Exception:
                continue
                
        # Si llegamos aquí, ninguno de los recuentos funcionó
        raise ValueError("Error de autenticación: El password o la llave de bóveda no coinciden.")


    
    @staticmethod
    def compute_key_checksum(key: bytes) -> str:
        """
        Calcula un checksum SHA-256 de una llave para validación rápida.
        
        Este checksum se puede almacenar localmente para verificar si la llave
        en memoria es la correcta ANTES de intentar desencriptar servicios.
        
        Args:
            key: Llave a verificar (generalmente vault_master_key)
            
        Returns:
            str: Hex string del hash SHA-256 (64 caracteres)
            
        Example:
            checksum = compute_key_checksum(vault_key)
            # checksum = '8a3f2e1b...' (64 chars hex)
            
            # Uso en validación:
            if stored_checksum == compute_key_checksum(current_key):
                logger.debug("Key matches checksum")
            else:
                logger.warning("Key mismatch - synchronization required")
                
        Security Note:
            - Este es solo un checksum, NO es secreto
            - Se puede almacenar en SQLite sin encriptar
            - Solo sirve para validación, no para derivar la llave
        """
        if not isinstance(key, bytes):
            raise TypeError("key must be bytes")
            
        return hashlib.sha256(key).hexdigest()
    
    @staticmethod
    def verify_key(key: bytes, expected_checksum: str) -> bool:
        """
        Verifica si una llave coincide con un checksum esperado.
        
        Args:
            key: Llave a verificar
            expected_checksum: Checksum esperado (hex string)
            
        Returns:
            bool: True si coincide, False si no
            
        Example:
            if CryptoEngine.verify_key(vault_key, stored_checksum):
                # Llave correcta, proceder a desencriptar
            else:
                # Llave incorrecta, mostrar mensaje al usuario
        """
        actual_checksum = CryptoEngine.compute_key_checksum(key)
        return actual_checksum == expected_checksum


# ============================================================================
# TESTING Y VALIDACIÓN (Solo para desarrollo)
# ============================================================================

def _test_crypto_engine():
    """
    Función de prueba para verificar que CryptoEngine funciona correctamente.
    Esta función NO debe ejecutarse en producción.
    """
    logger.debug("="*60)
    logger.debug("TESTING CRYPTOENGINE")
    logger.debug("="*60)
    
    # Test 1: Generar vault_master_key
    logger.debug("\n[TEST 1] Generating vault_master_key...")
    vault_key = CryptoEngine.generate_vault_master_key()
    logger.debug(f"[OK] Generated: {len(vault_key)} bytes")
    assert len(vault_key) == 32
    
    # Test 2: Wrap/Unwrap con password de usuario A
    logger.debug("\n[TEST 2] Wrap/Unwrap with User A...")
    user_a_password = "password_A_test"
    user_a_salt = os.urandom(16)
    wrapped_a = CryptoEngine.wrap_vault_key(vault_key, user_a_password, user_a_salt)
    logger.debug(f"[OK] Wrapped (A): {len(wrapped_a)} bytes")
    assert len(wrapped_a) == 60  # 12 nonce + 32 plaintext + 16 GCM tag
    
    unwrapped_a = CryptoEngine.unwrap_vault_key(wrapped_a, user_a_password, user_a_salt)
    logger.debug(f"[OK] Unwrapped (A): {len(unwrapped_a)} bytes")
    assert unwrapped_a == vault_key
    logger.debug("[OK] User A recovered vault_key successfully")
    
    # Test 3: Wrap/Unwrap con password de usuario B
    logger.debug("\n[TEST 3] Wrap/Unwrap with User B...")
    user_b_password = "password_B_test"
    user_b_salt = os.urandom(16)
    
    wrapped_b = CryptoEngine.wrap_vault_key(vault_key, user_b_password, user_b_salt)
    unwrapped_b = CryptoEngine.unwrap_vault_key(wrapped_b, user_b_password, user_b_salt)
    assert unwrapped_b == vault_key
    logger.debug("[OK] User B recovered THE SAME vault_key")
    
    # Test 4: Ambos usuarios tienen la MISMA llave
    logger.debug("\n[TEST 4] Verifying both share the same key...")
    assert unwrapped_a == unwrapped_b == vault_key
    logger.debug("[OK] unwrapped_a == unwrapped_b == vault_key")
    logger.debug("[OK] SUCCESS: Both users share the same master key")
    
    # Test 5: Checksum
    logger.debug("\n[TEST 5] Calculating checksum...")
    checksum = CryptoEngine.compute_key_checksum(vault_key)
    logger.debug(f"[OK] Checksum: {checksum[:16]}...")
    assert CryptoEngine.verify_key(vault_key, checksum)
    logger.debug("[OK] Checksum verification successful")
    
    # Test 6: Password incorrecta debe fallar
    logger.debug("\n[TEST 6] Verifying incorrect password fails...")
    try:
        CryptoEngine.unwrap_vault_key(wrapped_a, "wrong_password", user_a_salt)
        logger.error("[FAIL] ERROR: Should have failed with wrong password")
        assert False
    except ValueError:
        logger.debug("[OK] Incorrect password correctly rejected")
    
    logger.debug("\n" + "="*60)
    logger.debug("ALL TESTS PASSED [OK]")
    logger.debug("="*60)


if __name__ == "__main__":
    # Ejecutar tests solo en desarrollo
    _test_crypto_engine()
