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
from typing import Any, Optional, Tuple, List, Dict
from src.infrastructure.security.rate_limiter import RateLimiter

# NEW: Argon2 support
try:
    from argon2 import PasswordHasher, Type
    from argon2.exceptions import VerifyMismatchError, InvalidHash
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    PasswordHasher = None
    Type = None
    logger = logging.getLogger(__name__)
    logger.warning("argon2-cffi not installed, falling back to PBKDF2 only")

# Import crypto configuration
try:
    from config.crypto_config import (
        ARGON2_ENABLED, ARGON2_TIME_COST, ARGON2_MEMORY_COST,
        ARGON2_PARALLELISM, ARGON2_HASH_LEN, ARGON2_SALT_LEN,
        ARGON2_PREFIX, USE_ARGON2_FOR_NEW_USERS
    )
except ImportError:
    # Fallback defaults if config not found
    ARGON2_ENABLED = False
    ARGON2_TIME_COST = 2
    ARGON2_MEMORY_COST = 32768
    ARGON2_PARALLELISM = 2
    ARGON2_HASH_LEN = 32
    ARGON2_SALT_LEN = 16
    ARGON2_PREFIX = "$argon2"
    USE_ARGON2_FOR_NEW_USERS = False

logger = logging.getLogger(__name__)

from config.config import AUTH_MAX_ATTEMPTS, AUTH_WINDOW_SECONDS
# [NEW] Global RateLimiter instance and registry
auth_limiter = RateLimiter(max_attempts=AUTH_MAX_ATTEMPTS, window_seconds=AUTH_WINDOW_SECONDS)
_limiters = [auth_limiter]

def rate_limit(max_attempts=AUTH_MAX_ATTEMPTS, window=AUTH_WINDOW_SECONDS):
    """
    Decorador para prevenir ataques de fuerza bruta/timing.
    Usa el nombre de la función como clave para evitar bypass mediante variación de parámetros.
    """
    limiter = RateLimiter(max_attempts=max_attempts, window_seconds=window)
    _limiters.append(limiter)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # SECURITY FIX: Use function name only, not crypto material
            # This prevents bypass by varying salts/nonces
            key = f"{func.__name__}_global"
            
            if limiter.is_blocked(key):
                remaining = limiter.get_remaining_seconds(key)
                logger.warning(f"Rate limit exceeded for {func.__name__}. Blocked for {remaining}s")
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
    """Limpia el historial de intentos en todos los limitadores registrados."""
    for l in _limiters:
        with l.lock:
            l.attempts.clear()


class CryptoEngine:
    """
    Motor criptográfico centralizado para operaciones de Key Wrapping.
    Utiliza AESGCM (AES-256-GCM) para mantener compatibilidad con el sistema actual.
    """
    
    # --- CONSTANTES ---
    ARGON2_AVAILABLE = ARGON2_AVAILABLE
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
    
    # ===== ARGON2 PASSWORD HASHING (NEW) =====
    
    @staticmethod
    def _get_argon2_hasher():
        """Get configured Argon2 PasswordHasher instance."""
        if not ARGON2_AVAILABLE:
            raise RuntimeError("Argon2 not available - install argon2-cffi")
        
        return PasswordHasher(
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            salt_len=ARGON2_SALT_LEN,
            type=Type.ID  # Argon2id (hybrid mode)
        )
    
    @staticmethod
    def hash_user_password_argon2(password: str) -> str:
        """
        Hash password using Argon2id algorithm.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Argon2 hash string (includes algorithm, params, salt, and hash)
                 Format: $argon2id$v=19$m=32768,t=2,p=2$<salt>$<hash>
                 
        Example:
            hash = CryptoEngine.hash_user_password_argon2("mypassword")
            # hash = "$argon2id$v=19$m=32768,t=2,p=2$..."
        """
        if not ARGON2_ENABLED or not ARGON2_AVAILABLE:
            raise RuntimeError("Argon2 is not enabled or not available")
        
        ph = CryptoEngine._get_argon2_hasher()
        return ph.hash(password)
    
    @staticmethod
    def verify_user_password_argon2(password: str, stored_hash: str) -> bool:
        """
        Verify password against Argon2 hash.
        
        Args:
            password: Plain text password to verify
            stored_hash: Argon2 hash string from database
            
        Returns:
            bool: True if password matches
            
        Example:
            is_valid = CryptoEngine.verify_user_password_argon2(
                "mypassword",
                "$argon2id$v=19$m=32768,t=2,p=2$..."
            )
        """
        if not ARGON2_AVAILABLE:
            return False
        
        try:
            ph = CryptoEngine._get_argon2_hasher()
            ph.verify(stored_hash, password)
            return True
        except (VerifyMismatchError, InvalidHash):
            return False
        except Exception as e:
            logger.error(f"Argon2 verification error: {e}")
            return False
    
    @staticmethod
    def hash_user_password_auto(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """
        Hash password using the best available algorithm.
        
        - If Argon2 is enabled: Use Argon2id (salt embedded in hash)
        - Otherwise: Fall back to PBKDF2
        
        Args:
            password: Plain text password
            salt: Optional salt (only used for PBKDF2, ignored for Argon2)
            
        Returns:
            tuple: (hash_string, salt_bytes)
                   For Argon2: salt_bytes is empty (salt embedded in hash)
                   For PBKDF2: salt_bytes contains the salt
                   
        Example:
            hash, salt = CryptoEngine.hash_user_password_auto("password")
            # If Argon2: hash = "$argon2id$...", salt = b''
            # If PBKDF2: hash = "abc123...", salt = b'random16bytes'
        """
        if ARGON2_ENABLED and ARGON2_AVAILABLE and USE_ARGON2_FOR_NEW_USERS:
            # Use Argon2 (salt is embedded in the hash string)
            argon2_hash = CryptoEngine.hash_user_password_argon2(password)
            return argon2_hash, b''  # Empty salt (embedded in hash)
        else:
            # Fall back to PBKDF2
            return CryptoEngine.hash_user_password(password, salt)
    
    @staticmethod
    def verify_user_password_auto(password: str, salt: any, stored_hash: str) -> bool:
        """
        Verify password with automatic algorithm detection.
        
        Detects algorithm based on hash format:
        - Starts with "$argon2" → Use Argon2
        - Otherwise → Use PBKDF2
        
        Args:
            password: Plain text password to verify
            salt: Salt (only used for PBKDF2, ignored for Argon2)
            stored_hash: Hash string from database
            
        Returns:
            bool: True if password matches
            
        Example:
            # Argon2 hash
            is_valid = CryptoEngine.verify_user_password_auto(
                "password", None, "$argon2id$v=19$..."
            )
            
            # PBKDF2 hash
            is_valid = CryptoEngine.verify_user_password_auto(
                "password", salt_bytes, "abc123..."
            )
        """
        if not stored_hash:
            return False
        
        # Detect algorithm by hash prefix
        if stored_hash.startswith(ARGON2_PREFIX):
            # Argon2 hash
            return CryptoEngine.verify_user_password_argon2(password, stored_hash)
        else:
            # PBKDF2 hash (legacy) - normalize salt to bytes
            if not salt:
                return False
            
            # Convert salt to bytes if needed
            if isinstance(salt, str):
                try:
                    salt_bytes = bytes.fromhex(salt)
                except ValueError:
                    # If not hex, try encoding
                    salt_bytes = salt.encode('utf-8')
            elif isinstance(salt, (bytes, bytearray)):
                salt_bytes = bytes(salt)
            elif hasattr(salt, '__bytes__'):
                salt_bytes = bytes(salt)
            else:
                logger.error(f"Invalid salt type: {type(salt)}")
                return False
            
            return CryptoEngine.verify_user_password(password, salt_bytes, stored_hash)
    
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
    @staticmethod
    def derive_kek_argon2id(password: str, salt: bytes, memory_cost: int = 65536, time_cost: int = 2, parallelism: int = 1) -> bytes:
        """
        [GOD-LEVEL] Derives a KEK using Argon2id (resistant to GPU/ASIC attacks).
        Default: 64MB RAM consumption per derivation.
        """
        if not ARGON2_AVAILABLE:
            raise RuntimeError("Argon2 not available for KEK derivation")
            
        from argon2.low_level import hash_secret_raw, Type
        return hash_secret_raw(
            password.encode(), 
            salt,
            time_cost=time_cost, 
            memory_cost=memory_cost,
            parallelism=parallelism, 
            hash_len=CryptoEngine.KEY_SIZE, 
            type=Type.ID
        )

    @staticmethod
    @rate_limit(max_attempts=20, window=30)
    def unwrap_vault_key(wrapped_key: bytes, user_password: str, user_salt: bytes) -> Tuple[bytes, str]:
        """
        Desencripta la vault_master_key usando la password del usuario.
        [ULTRA RECOVERY] Soporta Argon2id y múltiples recuentos de PBKDF2.
        Returns: (decrypted_key, algorithm_used)
        """
        if not isinstance(wrapped_key, bytes):
            raise TypeError("wrapped_key must be bytes")
        if len(wrapped_key) < CryptoEngine.NONCE_SIZE + CryptoEngine.KEY_SIZE:
            raise ValueError("wrapped_key is too short")

        nonce = wrapped_key[:CryptoEngine.NONCE_SIZE]
        ciphertext = wrapped_key[CryptoEngine.NONCE_SIZE:]
        
        # 1. Try Argon2id (New Standard)
        if ARGON2_AVAILABLE:
            try:
                kek = CryptoEngine.derive_kek_argon2id(user_password, user_salt)
                aes_gcm = AESGCM(kek)
                return aes_gcm.decrypt(nonce, ciphertext, None), "argon2id"
            except Exception:
                pass

        # 2. Try PBKDF2 iterations (Legacy & Forensic Fallback)
        for iter_count in [100000, 600000, 10000, 1000]:
            try:
                kek = CryptoEngine.derive_kek_from_password(user_password, user_salt, iterations=iter_count)
                aes_gcm = AESGCM(kek)
                return aes_gcm.decrypt(nonce, ciphertext, None), "pbkdf2"
            except Exception:
                continue
                
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
