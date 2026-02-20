import os
import sys
from pathlib import Path

# Añadir src al path para poder importar
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.secure_memory import SecureBytes

def test_secure_bytes_logic():
    print("[Test] Verificando SecureBytes...")
    pattern = b"\xAA" * 32
    sb = SecureBytes(pattern)
    
    # Pruebas de acceso
    assert sb.get_copy() == pattern
    assert sb.get_raw() == pattern
    print("[OK] Datos accesibles inicialmente.")
    
    # Prueba de limpieza
    sb.clear()
    assert sb.get_copy() is None
    assert sb.get_raw() is None
    assert sb._cleared is True
    print("[OK] Datos inaccesibles tras clear().")
    
    # Prueba de context manager
    with SecureBytes(b"secret") as sb2:
        assert sb2.get_copy() == b"secret"
    assert sb2.get_copy() is None
    print("[OK] Limpieza automática vía Context Manager.")

if __name__ == "__main__":
    try:
        test_secure_bytes_logic()
        print("\n[RESULTADO] Todas las pruebas de lógica de memoria pasaron exitosamente.")
    except Exception as e:
        print(f"\n[ERROR] Fallo en la verificación de memoria: {e}")
        sys.exit(1)
