from argon2 import PasswordHasher, Type  # << nuevo
from argon2.low_level import hash_secret_raw
import os, ctypes, gc, multiprocessing

SALT_LEN = 16
KEY_LEN  = 32
TIME_COST = 15
MEMORY_COST = 128*1024
PARALLELISM = multiprocessing.cpu_count()

def derive_key(password: str, salt: bytes) -> bytes:
    # Use hash_secret_raw to get the raw bytes directly
    key = bytearray(hash_secret_raw(password.encode(), salt, TIME_COST, MEMORY_COST, PARALLELISM, KEY_LEN, type=Type.ID))
    try:
        return bytes(key)
    finally:
        ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(key)), 0, len(key))
        gc.collect()

def generate_salt() -> bytes:
    return os.urandom(SALT_LEN)
