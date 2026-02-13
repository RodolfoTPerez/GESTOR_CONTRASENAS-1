from dataclasses import dataclass
from typing import Final
from uuid import UUID

NONCE_LEN: Final = 12
TAG_LEN: Final = 16

@dataclass(frozen=True, slots=True)
class EncryptedSecret:
    id: UUID
    service: str
    username: str
    ciphertext: bytes
    nonce: bytes
    salt: bytes
