# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la privacidad compartida en PassGuardian.
Verifica que:
- Los servicios PUBLICOS (is_private=0) son visibles para todos
- Los servicios PRIVADOS (is_private=1) solo los ve el dueno
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.user_manager import UserManager
from src.infrastructure.crypto_engine import reset_rate_limits

def test_shared_privacy():
    """Prueba la privacidad compartida del sistema."""
    # Reset limiters to avoid interference from other tests
    reset_rate_limits()
    
    print("="*70)
    print(" TEST DE PRIVACIDAD COMPARTIDA - PassGuardian")
    print("="*70)
    
    # Crear instancia de SecretsManager
    sm = SecretsManager(None)
    um = UserManager(sm)
    
    # --- CLEANUP PREVIO (Para garantizar estado fresco) ---
    print("\n[CLEANUP] Eliminando usuarios de prueba anteriores...")
    try:
        # 1. Supabase
        um.supabase.table("users").delete().in_("username", ["RODOLFO", "KIKI"]).execute()
        
        # 2. Local DBs (Archivos)
        from src.infrastructure.config.path_manager import PathManager
        for u in ["rodolfo", "kiki"]:
            db_path = PathManager.get_user_db(u)
            if db_path.exists():
                try: 
                    os.remove(db_path)
                    print(f"   [DEL] {db_path.name}")
                except: pass
                
        # 3. Perfiles Locales (vultrax.db)
        # Esto asegura que el login local no intente usar credenciales viejas
        sm.users.conn.execute("DELETE FROM users WHERE username IN ('RODOLFO', 'KIKI')")
        sm.users.conn.commit()
    except Exception as e:
        print(f"   [WARN] Cleanup error (non-fatal): {e}")

    
    # Crear usuarios de prueba
    print("\n1. Configurando usuarios de prueba...")
    
    # Usuario RODOLFO (admin)
    try:
        um.add_new_user("RODOLFO", "admin", "password123")
        print("   [OK] Usuario RODOLFO (admin) creado")
    except Exception as e:
        print(f"   [INFO] RODOLFO ya existe")
    
    # Usuario KIKI (user)
    try:
        um.add_new_user("KIKI", "user", "password456")
        print("   [OK] Usuario KIKI (user) creado")
    except Exception as e:
        print(f"   [INFO] KIKI ya existe")
    
    # RODOLFO agrega servicios
    print("\n2. RODOLFO agrega servicios...")
    sm.set_active_user("RODOLFO", "password123")
    sm.clear_local_secrets()
    
    # RODOLFO: 1 publico (compartido) + 1 privado (solo el)
    sm.add_secret("Gmail Corporativo", "empresa@gmail.com", "pass_gmail_corp", 
                  "Email del equipo", is_private=0)
    sm.add_secret("Cuenta Bancaria Personal RODOLFO", "rodolfo_banco", "pass_banco_rodolfo", 
                  "Banco privado", is_private=1)
    
    rodolfo_services = sm.get_all()
    print(f"   [OK] RODOLFO creo {len(rodolfo_services)} servicios:")
    for s in rodolfo_services:
        privacy = "PUBLICO (compartido)" if s['is_private'] == 0 else "PRIVADO (solo el)"
        print(f"      - {s['service']} [{privacy}]")
    
    # KIKI agrega servicios
    print("\n3. KIKI agrega servicios...")
    sm.set_active_user("KIKI", "password456")
    sm.clear_local_secrets()
    
    # KIKI: 1 publico (compartido) + 1 privado (solo ella)
    sm.add_secret("Dropbox del Equipo", "equipo@dropbox.com", "pass_dropbox_equipo", 
                  "Storage compartido", is_private=0)
    sm.add_secret("Netflix Personal KIKI", "kiki_netflix", "pass_netflix_kiki", 
                  "Netflix privado", is_private=1)
    
    kiki_services = sm.get_all()
    print(f"   [OK] KIKI creo {len(kiki_services)} servicios:")
    for s in kiki_services:
        privacy = "PUBLICO (compartido)" if s['is_private'] == 0 else "PRIVADO (solo ella)"
        print(f"      - {s['service']} [{privacy}]")
    
    # Verificar que KIKI ve correctamente
    print("\n4. Verificando vista de KIKI...")
    sm.set_active_user("KIKI", "password456")
    kiki_view = sm.get_all()
    
    print(f"   KIKI ve {len(kiki_view)} servicios:")
    for s in kiki_view:
        privacy = "PUBLICO" if s['is_private'] == 0 else "PRIVADO"
        owner = s.get('owner_name', 'Unknown')
        print(f"      - {s['service']} [{privacy}] - Dueno: {owner}")
    
    # Verificaciones de KIKI
    kiki_public_count = sum(1 for s in kiki_view if s['is_private'] == 0)
    kiki_private_count = sum(1 for s in kiki_view if s['is_private'] == 1)
    has_rodolfo_public = any('Gmail Corporativo' in s['service'] for s in kiki_view)
    has_rodolfo_private = any('Bancaria Personal RODOLFO' in s['service'] for s in kiki_view)
    
    print(f"\n   Analisis de KIKI:")
    print(f"   - Ve {kiki_public_count} servicios publicos (debe ser 2: Gmail + Dropbox)")
    print(f"   - Ve {kiki_private_count} servicios privados (debe ser 1: solo Netflix)")
    print(f"   - Ve 'Gmail Corporativo' de RODOLFO? {'SI' if has_rodolfo_public else 'NO'} (debe ser SI)")
    print(f"   - Ve 'Cuenta Bancaria' de RODOLFO? {'SI' if has_rodolfo_private else 'NO'} (debe ser NO)")
    
    kiki_ok = (kiki_public_count == 2 and kiki_private_count == 1 and 
               has_rodolfo_public and not has_rodolfo_private)
    
    if kiki_ok:
        print("   [CORRECTO] KIKI ve servicios publicos compartidos pero NO privados de otros")
    else:
        print("   [ERROR] La privacidad de KIKI no funciona correctamente!")
        return False
    
    # Verificar que RODOLFO ve correctamente
    print("\n5. Verificando vista de RODOLFO (admin)...")
    sm.set_active_user("RODOLFO", "password123")
    rodolfo_view = sm.get_all()
    
    print(f"   RODOLFO ve {len(rodolfo_view)} servicios:")
    for s in rodolfo_view:
        privacy = "PUBLICO" if s['is_private'] == 0 else "PRIVADO"
        owner = s.get('owner_name', 'Unknown')
        print(f"      - {s['service']} [{privacy}] - Dueno: {owner}")
    
    # Verificaciones de RODOLFO
    rodolfo_public_count = sum(1 for s in rodolfo_view if s['is_private'] == 0)
    rodolfo_private_count = sum(1 for s in rodolfo_view if s['is_private'] == 1)
    has_kiki_public = any('Dropbox del Equipo' in s['service'] for s in rodolfo_view)
    has_kiki_private = any('Netflix Personal KIKI' in s['service'] for s in rodolfo_view)
    
    print(f"\n   Analisis de RODOLFO:")
    print(f"   - Ve {rodolfo_public_count} servicios publicos (debe ser 2: Gmail + Dropbox)")
    print(f"   - Ve {rodolfo_private_count} servicios privados (debe ser 1: solo Banco)")
    print(f"   - Ve 'Dropbox del Equipo' de KIKI? {'SI' if has_kiki_public else 'NO'} (debe ser SI)")
    print(f"   - Ve 'Netflix' de KIKI? {'SI' if has_kiki_private else 'NO'} (debe ser NO)")
    
    rodolfo_ok = (rodolfo_public_count == 2 and rodolfo_private_count == 1 and 
                  has_kiki_public and not has_kiki_private)
    
    if rodolfo_ok:
        print("   [CORRECTO] RODOLFO ve servicios publicos compartidos pero NO privados de KIKI")
    else:
        print("   [ERROR] La privacidad de RODOLFO no funciona correctamente!")
        return False
    
    # Resumen final
    print("\n" + "="*70)
    print(" [EXITO] TODAS LAS PRUEBAS PASARON")
    print("         PRIVACIDAD COMPARTIDA FUNCIONANDO CORRECTAMENTE")
    print("="*70)
    print("\nModelo de Privacidad Confirmado:")
    print("   * Servicios PUBLICOS (is_private=0):")
    print("     - Gmail Corporativo (RODOLFO) -> Visible para todos")
    print("     - Dropbox del Equipo (KIKI) -> Visible para todos")
    print("")
    print("   * Servicios PRIVADOS (is_private=1):")
    print("     - Cuenta Bancaria (RODOLFO) -> Solo RODOLFO lo ve")
    print("     - Netflix (KIKI) -> Solo KIKI lo ve")
    print("")
    print("   * Administrador NO tiene privilegios especiales de visualizacion")
    print("="*70)
    
    return True

if __name__ == "__main__":
    try:
        success = test_shared_privacy()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
