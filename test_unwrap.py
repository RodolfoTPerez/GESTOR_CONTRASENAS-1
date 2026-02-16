
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.infrastructure.crypto_engine import CryptoEngine, reset_rate_limits

def test():
    print("Testing unwrap_vault_key with rate limit...")
    import getpass
    password = getpass.getpass("Ingrese contraseña (testpassword): ")
    salt = os.urandom(16)
    master_key = os.urandom(32)
    
    print("Wrapping key...")
    wrapped = CryptoEngine.wrap_vault_key(master_key, password, salt)
    print(f"Wrapped key length: {len(wrapped)}")
    
    reset_rate_limits()
    
    print("Unwrapping key (Attempt 1)...")
    try:
        start = time.time()
        unwrapped = CryptoEngine.unwrap_vault_key(wrapped, password, salt)
        print(f"Unwrapped in {time.time() - start:.4f}s")
        assert unwrapped == master_key
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

    print("Unwrapping key (Attempt 2)...")
    try:
        start = time.time()
        unwrapped = CryptoEngine.unwrap_vault_key(wrapped, password, salt)
        print(f"Unwrapped in {time.time() - start:.4f}s")
    except Exception as e:
        print(f"Error (Expected if rate limited, but max is 5): {e}")

if __name__ == "__main__":
    test()
