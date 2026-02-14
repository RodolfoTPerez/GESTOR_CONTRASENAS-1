#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REPARACIÓN OFICIAL: Sincronización de Tabla vault_access
========================================================
Este script utiliza la infraestructura oficial de PassGuardian para:
1. Desencriptar la llave de bóveda actual del usuario.
2. Asegurar que la tabla 'vault_access' esté correctamente poblada.
3. Garantizar compatibilidad con el nuevo sistema de múltiples bóvedas.
"""

import sys
import os
import logging
import getpass
from pathlib import Path

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Asegurar que el path del proyecto esté incluido
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.infrastructure.database.db_manager import DBManager
    from src.infrastructure.repositories.user_repo import UserRepository
    from src.infrastructure.crypto_engine import CryptoEngine
except ImportError as e:
    print(f"❌ Error: No se pudo importar la infraestructura de la app. {e}")
    sys.exit(1)

def run_fix():
    print("="*70)
    print("🛠️  REPARACIÓN OFICIAL: Sincronización vault_access")
    print("="*70)
    print()

    username = "RODOLFO" # Puedes cambiar esto por un input(prefijo)
    username_clean = username.upper().replace(" ", "")
    
    # 1. Conectar usando DBManager (Esto asegura que la tabla vault_access exista)
    print(f"🔍 Inicializando base de datos para {username_clean}...")
    db = DBManager(username)
    user_repo = UserRepository(db)
    
    # 2. Obtener perfil actual
    profile = user_repo.get_profile(username_clean)
    if not profile:
        print(f"❌ No se encontró el perfil de {username_clean} en la DB local.")
        db.close()
        return

    v_id = profile.get("vault_id")
    v_salt = profile.get("vault_salt")
    w_v_key = profile.get("wrapped_vault_key")

    print(f"📊 Estado Actual:")
    print(f"   Vault ID: {v_id}")
    print(f"   Vault Salt: {'✅ Presente' if v_salt else '❌ Ausente'}")
    print(f"   Wrapped Key: {'✅ Presente' if w_v_key else '❌ Ausente'}")
    print()

    if not v_salt or not w_v_key:
        print("❌ Error: Faltan componentes críticos para desencriptar la llave.")
        db.close()
        return

    # 3. Validar llave
    print("🔐 Ingrese su contraseña de PassGuardian para validar:")
    password = getpass.getpass("Contraseña: ")

    try:
        print("\n🔓 Intentando unwrap oficial...")
        # Asegurar bytes
        if isinstance(v_salt, (str, bytes)):
            if isinstance(v_salt, str) and v_salt.startswith("\\x"):
                 v_salt_bytes = bytes.fromhex(v_salt[2:])
            elif isinstance(v_salt, str):
                 try: v_salt_bytes = bytes.fromhex(v_salt)
                 except: v_salt_bytes = v_salt.encode()
            else:
                 v_salt_bytes = v_salt
        
        # Usar CryptoEngine oficial
        # Nota: unwrap_vault_key requiere wrapped_key, password, salt
        # Devuelve la master_key plana de 32 bytes
        vault_key_plain = CryptoEngine.unwrap_vault_key(w_v_key, password, v_salt_bytes)
        
        print("✅ Llave desencriptada con éxito.")
        
        # 4. Actualizar tabla vault_access usando el repositorio oficial
        # UserRepository.update_vault_access ahora escribe en ambas tablas y respeta el esquema
        print("💾 Persistiendo en vault_access (Esquema Oficial)...")
        success = user_repo.update_vault_access(username_clean, v_id, w_v_key)
        
        if success:
            print("\n" + "="*70)
            print("🎉 REPARACIÓN COMPLETADA CON ÉXITO")
            print("="*70)
            print("1. La tabla 'vault_access' ha sido sincronizada.")
            print("2. Se mantiene compatibilidad con el esquema legacy.")
            print("3. El sistema de sincronización podrá leer esta llave correctamente.")
        else:
            print("❌ Error al guardar en la base de datos.")

    except Exception as e:
        print(f"\n❌ Error de Autenticación o Corrupción: {e}")
        print("Verifique que la contraseña sea la correcta.")

    finally:
        db.close()

if __name__ == "__main__":
    run_fix()
