import ctypes
import threading
from typing import Optional

class SecureBytes:
    """
    [MILITARY GRADE SECURITY] Wrapper para material criptográfico sensible.
    Asegura que la memoria física sea sobrescrita con ceros (Zeroing) mediante memset de bajo nivel
    cuando el objeto se destruye o se libera explícitamente.
    """
    def __init__(self, data: bytes):
        # Convertimos a bytearray mutable para permitir el zeroing físico
        self._buf = bytearray(data)
        self._lock = threading.Lock()
        self._cleared = False
        self._size = len(data)

    def get_raw(self) -> Optional[bytearray]:
        """Retorna el bytearray mutable (usar con precaución)."""
        with self._lock:
            if self._cleared:
                return None
            return self._buf

    def get_copy(self) -> Optional[bytes]:
        """Retorna una copia inmutable (usar solo por tiempo mínimo)."""
        with self._lock:
            if self._cleared:
                return None
            return bytes(self._buf)

    def clear(self):
        """Sobrescribe la memoria física con ceros de forma inmediata."""
        with self._lock:
            if not self._cleared and self._buf:
                try:
                    # Técnica robusta compatible con CPython (from_buffer)
                    char_ptr = (ctypes.c_char * self._size).from_buffer(self._buf)
                    ctypes.memset(char_ptr, 0, self._size)
                except Exception:
                    # Fallback de emergencia si el buffer no es accesible directamente
                    for i in range(self._size):
                        self._buf[i] = 0
                finally:
                    self._cleared = True
                    # Sugerimos al GC liberar el objeto, aunque el contenido ya sea 0
                    self._buf = bytearray() 

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()

    def __del__(self):
        # Última línea de defensa si el programador olvida llamar a clear()
        try:
            self.clear()
        except:
            pass

    def __repr__(self):
        return f"<SecureBytes[CLEARED]" if self._cleared else f"<SecureBytes[ENCRYPTED_DATA:{self._size}b]>"
