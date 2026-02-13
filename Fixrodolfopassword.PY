#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO Y REPARACIÓN DE PASSWORD - RODOLFO
===============================================

Este script diagnostica y repara problemas de autenticación.

Uso:
    python fix_rodolfo_password.py
"""

import sys
import os
import sqlite3
import hashlib
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def hash_password_100k(password: str, salt: str) -> str:
    """
    Hash password usando PBKDF2 con 100,000 iteraciones (método actual).
    """
    # Convertir salt de hex a bytes
    salt_bytes = bytes.fromhex(salt)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt_bytes,
        iterations=100000,
        backend=default_backend()
    )
    
    key = kdf.derive(password.encode('utf-8'))
    return key.hex()

def hash_password_legacy(password: str, salt: str) -> str:
    """
    Hash password usando método legacy (si existía antes).
    """
    # Método simple SHA256
    return hashlib.sha256(f"{password}{salt}".encode('utf-8')).hexdigest()

def get_user_data(username: str):
    """
    Obtiene los datos del usuario desde la base de datos.
    """
    db_path = Path(f"data/vault_{username.lower()}.db")
    
    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Obtener datos del usuario
        cursor.execute("""
            SELECT username, password_hash, salt, vault_salt, role
            FROM users
            WHERE username = ?
        """, (username.upper(),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'username': row[0],
                'password_hash': row[1],
                'salt': row[2],
                'vault_salt': row[3],
                'role': row[4]
            }
        return None
    except Exception as e:
        print(f"❌ Error leyendo base de datos: {e}")
        return None

def update_password(username: str, new_password: str, salt: str):
    """
    Actualiza la contraseña en la base de datos.
    """
    db_path = Path(f"data/vault_{username.lower()}.db")
    
    # Calcular nuevo hash
    new_hash = hash_password_100k(new_password, salt)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET password_hash = ?
            WHERE username = ?
        """, (new_hash, username.upper()))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ Error actualizando contraseña: {e}")
        return False

def main():
    print("="*70)
    print("🔧 DIAGNÓSTICO Y REPARACIÓN DE PASSWORD - VULTRAX CORE")
    print("="*70)
    print()
    
    username = "RODOLFO"
    
    # 1. Obtener datos actuales
    print(f"📊 Obteniendo datos de usuario: {username}")
    user_data = get_user_data(username)
    
    if not user_data:
        print(f"❌ No se pudo obtener datos del usuario {username}")
        return 1
    
    print(f"✅ Datos encontrados:")
    print(f"   Username: {user_data['username']}")
    print(f"   Salt: {user_data['salt']}")
    print(f"   Hash actual: {user_data['password_hash'][:16]}...")
    print(f"   Role: {user_data['role']}")
    print()
    
    # 2. Pedir contraseña actual para verificar
    print("🔐 Verificación de contraseña")
    print("-" * 70)
    current_password = input("Ingrese la contraseña que está intentando usar: ")
    
    # 3. Probar con 100k iteraciones (método actual)
    print()
    print("🧪 Probando con PBKDF2 (100,000 iteraciones)...")
    calc_hash_100k = hash_password_100k(current_password, user_data['salt'])
    
    print(f"   Hash calculado: {calc_hash_100k[:16]}...")
    print(f"   Hash almacenado: {user_data['password_hash'][:16]}...")
    
    if calc_hash_100k == user_data['password_hash']:
        print("✅ ¡La contraseña es CORRECTA con el método actual!")
        print("   El problema no está en la contraseña.")
        print()
        print("🔍 Posibles causas:")
        print("   1. Error en la lógica de verify_password en user_manager.py")
        print("   2. Problema de encoding UTF-8")
        print("   3. Salt corrupto en memoria vs base de datos")
        print()
        print("💡 SOLUCIÓN:")
        print("   Revise el código en src/infrastructure/user_manager.py")
        print("   Líneas ~550-600 (función verify_password)")
        return 0
    
    print("❌ La contraseña NO coincide con el método actual")
    print()
    
    # 4. Probar con método legacy
    print("🧪 Probando con método legacy (SHA256 simple)...")
    calc_hash_legacy = hash_password_legacy(current_password, user_data['salt'])
    
    if calc_hash_legacy == user_data['password_hash']:
        print("✅ ¡La contraseña coincide con el método LEGACY!")
        print()
        print("🔧 PROBLEMA IDENTIFICADO:")
        print("   El hash en la BD usa un método antiguo (SHA256 simple)")
        print("   pero el código actual usa PBKDF2 con 100k iteraciones.")
        print()
        
        # Ofrecer migración
        print("💾 ¿Desea MIGRAR la contraseña al nuevo formato?")
        print("   Esto actualizará el hash en la base de datos.")
        response = input("   (S/N): ").strip().upper()
        
        if response == 'S':
            print()
            print("🔄 Migrando contraseña...")
            if update_password(username, current_password, user_data['salt']):
                print("✅ ¡Contraseña migrada exitosamente!")
                print()
                print("🎉 Ahora puede iniciar sesión normalmente.")
                return 0
            else:
                print("❌ Error durante la migración")
                return 1
        else:
            print("❌ Migración cancelada")
            return 1
    
    print("❌ La contraseña NO coincide con ningún método conocido")
    print()
    
    # 5. Ofrecer reset de contraseña
    print("="*70)
    print("🆘 OPCIONES DE RECUPERACIÓN")
    print("="*70)
    print()
    print("1. RESET DE CONTRASEÑA - Establecer nueva contraseña")
    print("2. SALIR - Cancelar operación")
    print()
    
    choice = input("Seleccione opción (1/2): ").strip()
    
    if choice == "1":
        print()
        print("🔐 RESET DE CONTRASEÑA")
        print("-" * 70)
        new_password = input("Ingrese NUEVA contraseña: ")
        confirm = input("Confirme NUEVA contraseña: ")
        
        if new_password != confirm:
            print("❌ Las contraseñas no coinciden")
            return 1
        
        if len(new_password) < 8:
            print("❌ La contraseña debe tener al menos 8 caracteres")
            return 1
        
        print()
        print("⚠️  ADVERTENCIA: Esta operación cambiará su contraseña maestra.")
        print("   Asegúrese de recordar la nueva contraseña.")
        final_confirm = input("   ¿Continuar? (SI/NO): ").strip().upper()
        
        if final_confirm == "SI":
            print()
            print("🔄 Actualizando contraseña...")
            if update_password(username, new_password, user_data['salt']):
                print("✅ ¡Contraseña actualizada exitosamente!")
                print()
                print("🎉 Puede iniciar sesión con su nueva contraseña.")
                print()
                print("📝 NUEVA CONTRASEÑA:")
                print(f"   {new_password}")
                print()
                print("   ⚠️  Guarde esta contraseña en un lugar seguro.")
                return 0
            else:
                print("❌ Error actualizando contraseña")
                return 1
        else:
            print("❌ Operación cancelada")
            return 1
    
    print("❌ Operación cancelada")
    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)