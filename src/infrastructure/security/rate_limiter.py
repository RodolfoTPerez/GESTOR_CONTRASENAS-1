
import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """
    Provee una capa de protección contra ataques de fuerza bruta.
    Mantiene un registro granular (por llave/usuario) de intentos fallidos.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self.attempts = defaultdict(list)
        self.lock = Lock()

    def is_blocked(self, key: str) -> bool:
        """Verifica si una llave específica está bloqueada."""
        with self.lock:
            now = time.time()
            # Limpiar intentos fuera de la ventana
            self.attempts[key] = [t for t in self.attempts[key] if now - t < self.window]
            
            return len(self.attempts[key]) >= self.max_attempts

    def record_attempt(self, key: str):
        """Registra un nuevo intento para la llave."""
        with self.lock:
            self.attempts[key].append(time.time())

    def reset(self, key: str):
        """Limpia el historial de intentos para una llave (ej. tras login exitoso)."""
        with self.lock:
            if key in self.attempts:
                del self.attempts[key]

    def get_remaining_seconds(self, key: str) -> int:
        """Calcula cuántos segundos quedan para que expire el bloqueo."""
        with self.lock:
            if not self.attempts[key]:
                 return 0
            oldest = self.attempts[key][0]
            remaining = int(self.window - (time.time() - oldest))
            return max(0, remaining)
