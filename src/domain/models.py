from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

# Tabla master
@dataclass
class Master:
    id: int
    created_at: datetime
    verifier: str
    nonce: str
    failed: int
    locked_until: float
    salt: str
    email: str

# Tabla totp
@dataclass
class TOTP:
    id: int
    created_at: datetime
    secret: str  # Base32

# Tabla users
@dataclass
class User:
    id: int
    created_at: datetime
    username: str
    role: str
    active: bool

# Tabla sessions
@dataclass
class Session:
    id: UUID
    session_token: str
    user_id: str
    ip_address: str
    device_info: str
    created_at: datetime
    last_activity: datetime

# Tabla secrets (credenciales)
@dataclass
class Secret:
    id: UUID
    created_at: datetime
    service: str
    user: str
    secret: bytes  # cifrado AES-GCM
    nonce: bytes
