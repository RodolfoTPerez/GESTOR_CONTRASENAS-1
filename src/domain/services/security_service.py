import os
import hashlib
import base64
import re
import logging
from typing import Optional, List, Tuple, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.infrastructure.crypto_engine import CryptoEngine

logger = logging.getLogger(__name__)

class SecurityService:
    """
    Orchestrates high-level security operations and key wrapping policies.
    """
    def __init__(self) -> None:
        pass

    def ensure_bytes(self, data: any) -> Optional[bytes]:
        if data is None: return None
        if isinstance(data, (bytes, bytearray, memoryview)): return bytes(data)
        s = str(data).strip()
        if s.startswith("\\x") or s.startswith("\\\\x"):
            hex_str = s[2:] if s.startswith("\\x") else s[3:]
            try: return bytes.fromhex(hex_str)
            except Exception as e:
                logger.debug(f"Hex normalization failed for {hex_str[:10]}...: {e}")
        if len(s) >= 32 and all(c in "0123456789abcdefABCDEF" for c in s):
            try: return bytes.fromhex(s)
            except Exception as e:
                logger.debug(f"Hex-like normalization failed for {s[:10]}...: {e}")
        try:
            if 16 <= len(s) <= 128 and re.match(r'^[A-Za-z0-9+/=]+$', s):
                return base64.b64decode(s)
        except Exception as e:
            logger.debug(f"Base64 normalization failed: {e}")
        return s.encode('utf-8')

    def derive_keke(self, password: str, salt: bytes) -> bytes:
        return CryptoEngine.derive_kek_from_password(password, salt, CryptoEngine.DEFAULT_ITERATIONS)

    def decrypt_protected_key(self, protected_key_blob: any, kek: bytes) -> Optional[bytearray]:
        try:
            pk = self.ensure_bytes(protected_key_blob)
            if pk and len(pk) >= 28:
                return bytearray(AESGCM(kek).decrypt(pk[:12], pk[12:], None))
        except Exception as e:
            logger.debug(f"Protected key decryption failed: {e}")
        return None

    def encrypt_data(self, data_plain: str, key: bytes) -> Tuple[bytes, bytes, str]:
        nonce = os.urandom(12)
        encrypted = AESGCM(key).encrypt(nonce, data_plain.encode("utf-8"), None)
        integrity = hashlib.sha256(encrypted).hexdigest()
        return encrypted, nonce, integrity

    def decrypt_data(self, enc_data: bytes, nonce: bytes, candidate_keys: List[Union[bytes, bytearray]]) -> str:
        for k in candidate_keys:
            if not k or len(k) != 32: continue
            try:
                dec_bytes = AESGCM(k).decrypt(nonce, enc_data, None)
                return dec_bytes.decode("utf-8")
            except Exception as e:
                logger.debug(f"Candidate key decryption failed: {e}")
                continue
        return "[Bloqueado 🔑]"

    def wrap_key(self, key_to_wrap: any, password: str, salt: any) -> bytes:
        return CryptoEngine.wrap_vault_key(self.ensure_bytes(key_to_wrap), password, self.ensure_bytes(salt))

    def unwrap_key(self, wrapped_data: any, password: str, salt: any) -> bytes:
        return CryptoEngine.unwrap_vault_key(self.ensure_bytes(wrapped_data), password, self.ensure_bytes(salt))
