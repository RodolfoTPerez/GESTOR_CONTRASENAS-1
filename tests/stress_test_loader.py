import time
import random
import string
from src.infrastructure.secrets_manager import SecretsManager
# Importamos el sync manager para forzar la subida real
from src.infrastructure.sync_manager import SyncManager 

def generate_pwd(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def run_stress_test_real(num_records=100):
    print(f"🔥 INICIANDO PRUEBA A FUEGO REAL: {num_records} REGISTROS")
    print("⚠️  ADVERTENCIA: Se sincronizará con Supabase en tiempo real.")
    
    db = SecretsManager()
    sync = SyncManager()
    
    start_time = time.time()
    
    for i in range(1, num_records + 1):
        svc = f"REAL_TEST_{i:03d}"
        usr = f"admin_test_{random.randint(100, 999)}"
        pwd = generate_pwd()
        
        # 1. Inserción Local
        db.add_secret(service=svc, username=usr, password=pwd, is_private=0)
        
        # 2. Forzamos Sincronización Inmediata (Fuego Real)
        # Aquí probamos si el hilo de red bloquea la app
        sync.upload_single_record(svc) 
        
        if i % 10 == 0:
            elapsed = time.time() - start_time
            print(f"🚀 [{i}/{num_records}] - Tiempo transcurrido: {elapsed:.2f}s")

    total_time = time.time() - start_time
    print("\n" + "█"*40)
    print(f"✅ RESULTADOS FINALES")
    print(f"⏱️ Tiempo Total: {total_time:.2f}s")
    print(f"📊 Promedio Red + Local: {total_time/num_records:.2f}s/req")
    print("█"*40)

if __name__ == "__main__":
    run_stress_test_real(100)