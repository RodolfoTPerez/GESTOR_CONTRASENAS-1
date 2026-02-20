import pytest
import os
import hashlib
from src.infrastructure.crypto_engine import CryptoEngine, reset_rate_limits

def test_password_hashing_pbkdf2():
    """Prueba el hashing de contraseñas usando PBKDF2."""
    password = "SafePassword123!"
    hash_hex, salt = CryptoEngine.hash_user_password(password)
    
    assert len(salt) == 16
    assert isinstance(hash_hex, str)
    assert len(hash_hex) == 64  # SHA-256 hex result
    
    # Verificar coincidencia
    assert CryptoEngine.verify_user_password(password, salt, hash_hex) is True
    # Verificar fallo con password incorrecta
    assert CryptoEngine.verify_user_password("WrongPassword", salt, hash_hex) is False

def test_password_hashing_argon2():
    """Prueba el hashing usando Argon2 (si está disponible)."""
    password = "ArgonSecret99!"
    try:
        hash_str = CryptoEngine.hash_user_password_argon2(password)
        assert hash_str.startswith("$argon2id$")
        assert CryptoEngine.verify_user_password_argon2(password, hash_str) is True
        assert CryptoEngine.verify_user_password_argon2("wrong", hash_str) is False
    except RuntimeError as e:
        if "Argon2 is not enabled" in str(e) or "Argon2 not available" in str(e):
            pytest.skip("Argon2 no está habilitado o instalado en este entorno")
        else:
            raise e

def test_password_auto_detection():
    """Verifica que el sistema detecte automáticamente el algoritmo (PBKDF2 vs Argon2)."""
    password = "UniversalSecret"
    
    # 1. Test PBKDF2 (Legacy)
    hash_pbkdf2, salt = CryptoEngine.hash_user_password(password)
    assert CryptoEngine.verify_user_password_auto(password, salt, hash_pbkdf2) is True
    
    # 2. Test Argon2 (Si disponible)
    try:
        hash_argon2 = CryptoEngine.hash_user_password_argon2(password)
        assert CryptoEngine.verify_user_password_auto(password, None, hash_argon2) is True
    except RuntimeError:
        pass

def test_vault_master_key_generation():
    """Verifica la generación de llaves maestras de bóveda."""
    key = CryptoEngine.generate_vault_master_key()
    assert len(key) == 32
    # Dos llaves no deben ser iguales
    key2 = CryptoEngine.generate_vault_master_key()
    assert key != key2

def test_key_checksum_verification():
    """Prueba el sistema de validación rápida por checksum."""
    key = os.urandom(32)
    checksum = CryptoEngine.compute_key_checksum(key)
    
    assert len(checksum) == 64
    assert CryptoEngine.verify_key(key, checksum) is True
    assert CryptoEngine.verify_key(os.urandom(32), checksum) is False

def test_vault_key_wrapping_roundtrip():
    """Prueba el ciclo completo de Wrap/Unwrap (corazón del sistema)."""
    vault_key = CryptoEngine.generate_vault_master_key()
    user_pwd = "UserMasterKey2026!"
    user_salt = os.urandom(16)
    
    # Wrap (Cifrar llave de bóveda con clave de usuario)
    wrapped = CryptoEngine.wrap_vault_key(vault_key, user_pwd, user_salt)
    assert len(wrapped) == 12 + 32 + 16  # Nonce(12) + Key(32) + Tag(16) = 60 bytes
    
    # Unwrap (Recuperar original)
    unwrapped, algo = CryptoEngine.unwrap_vault_key(wrapped, user_pwd, user_salt)
    assert unwrapped == vault_key
    assert algo in ["argon2id", "pbkdf2"]
    
    # Fallo con password incorrecta
    with pytest.raises(ValueError, match="Error de autenticación"):
        CryptoEngine.unwrap_vault_key(wrapped, "WrongPassword", user_salt)

def test_ultra_recovery_legacy_iterations():
    """Verifica que el sistema pueda recuperar llaves con recuentos de iteraciones antiguos."""
    vault_key = CryptoEngine.generate_vault_master_key()
    user_pwd = "LegacyPassword"
    user_salt = os.urandom(16)
    
    # Forzamos un wrap manual con 10,000 iteraciones (Legacy)
    from src.infrastructure.crypto_engine import AESGCM
    kek = CryptoEngine.derive_kek_from_password(user_pwd, user_salt, iterations=10000)
    nonce = os.urandom(12)
    aes = AESGCM(kek)
    ciphertext = aes.encrypt(nonce, vault_key, None)
    wrapped_legacy = nonce + ciphertext
    
    # unwrap_vault_key debe detectar y recuperar esto automáticamente mediante el loop de recuperación
    unwrapped, algo = CryptoEngine.unwrap_vault_key(wrapped_legacy, user_pwd, user_salt)
    assert unwrapped == vault_key
    assert algo == "pbkdf2"

def test_rate_limiter_protection():
    """Verifica que la protección contra fuerza bruta en unwrap funcione."""
    reset_rate_limits()
    wrapped = b'\x00' * 60
    salt = os.urandom(16)
    
    # El decorador rate_limit en unwrap_vault_key permite 20 intentos en 30s
    for i in range(20):
        try:
            CryptoEngine.unwrap_vault_key(wrapped, f"pwd_{i}", salt)
        except ValueError as e:
            if "Demasiados intentos" in str(e):
                pytest.fail("Rate limit bloqueó antes de alcanzar el límite configurado")
            # Debería fallar con "Error de autenticación" normalmente
            pass
            
    # El intento 21 deberia ser bloqueado por el RateLimiter
    with pytest.raises(ValueError, match="Demasiados intentos"):
        CryptoEngine.unwrap_vault_key(wrapped, "pwd_21", salt)
    
    reset_rate_limits()

def test_key_derivation_kek_consistency():
    """Asegura que la derivación de KEK sea determinística y robusta."""
    pwd = "consistent_password"
    salt = b"StaticSaltBytes12"
    
    kek1 = CryptoEngine.derive_kek_from_password(pwd, salt, iterations=100000)
    kek2 = CryptoEngine.derive_kek_from_password(pwd, salt, iterations=100000)
    
    assert kek1 == kek2
    assert len(kek1) == 32
    
    # Diferente iteración -> Diferente KEK
    kek3 = CryptoEngine.derive_kek_from_password(pwd, salt, iterations=100001)
    assert kek1 != kek3
