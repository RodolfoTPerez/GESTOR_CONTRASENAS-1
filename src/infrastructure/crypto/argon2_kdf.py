from argon2 import PasswordHasher, Type  # << nuevo
from argon2.low_level import hash_secret
import os, ctypes, gc, multiprocessing

SALT_LEN = 16
KEY_LEN  = 32
TIME_COST = 15
MEMORY_COST = 128*1024
PARALLELISM = multiprocessing.cpu_count()

def derive_key(password: str, salt: bytes) -> bytes:
    ph = PasswordHasher(
        time_cost=TIME_COST,
        memory_cost=MEMORY_COST,
        parallelism=PARALLELISM,
        hash_len=KEY_LEN,
        salt_len=SALT_LEN,
        type=Type.ID
    )
    # argon2-cffi devuelve un hash; tomamos los últimos 32 B
    raw = ph.hash(password, salt=salt).split('$')[-1]  # base64
    key = bytearray(hash_secret(password.encode(), salt, TIME_COST, MEMORY_COST, PARALLELISM, KEY_LEN, type=Type.ID))
    try:
        return bytes(key)
    finally:
        ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(key)), 0, len(key))
        gc.collect()

def generate_salt() -> bytes:
    return os.urandom(SALT_LEN)