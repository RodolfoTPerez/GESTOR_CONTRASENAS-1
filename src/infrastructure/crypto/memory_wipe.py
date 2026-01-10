import ctypes, gc

def secure_zero(b: bytearray) -> None:
    ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(b)), 0, len(b))
    gc.collect()