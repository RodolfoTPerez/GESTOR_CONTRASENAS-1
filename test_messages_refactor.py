import sys
import os

# Añadir el directorio raíz al path para poder importar src
sys.path.append(r"c:\PassGuardian_v2")

# Forzar salida UTF-8 para consola Windows (emojis)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.domain.messages import MESSAGES

def test_messages():
    print(f"Directorio de base: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Probar Español
    MESSAGES.LANG = "ES"
    print("\n--- TEST: ESPAÑOL ---")
    print(f"COMMON.TITLE_ERROR: {MESSAGES.COMMON.TITLE_ERROR}")
    print(f"DASHBOARD.SYNC: {MESSAGES.DASHBOARD.SYNC}")
    print(f"LOGIN.AppVersion: {MESSAGES.LOGIN.AppVersion}")
    
    # Probar Inglés
    MESSAGES.LANG = "EN"
    print("\n--- TEST: ENGLISH ---")
    print(f"COMMON.TITLE_ERROR: {MESSAGES.COMMON.TITLE_ERROR}")
    print(f"DASHBOARD.SYNC: {MESSAGES.DASHBOARD.SYNC}")
    print(f"LOGIN.AppVersion: {MESSAGES.LOGIN.AppVersion}")
    
    # Probar clave inexistente
    print("\n--- TEST: MISSING KEY ---")
    print(f"NON_EXISTENT.KEY: {MESSAGES.get('NON_EXISTENT', 'KEY')}")

if __name__ == "__main__":
    test_messages()
