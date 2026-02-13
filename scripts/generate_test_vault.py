#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Bóveda de Prueba para PassGuardian
================================================
Este script genera las llaves y SQL necesarios para crear
una bóveda de prueba en Supabase.

Ejecutar: python generate_test_vault.py
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.crypto_engine import CryptoEngine

def generate_test_vault():
    """Genera una bóveda de prueba con usuarios RODOLFO y KIKI."""
    
    print("="*70)
    print(" GENERADOR DE BÓVEDA DE PRUEBA - PassGuardian")
    print("="*70)
    
    # ========================================
    # PASO 1: Generar vault_master_key
    # ========================================
    print("\n[PASO 1] Generando vault_master_key para Bóveda A...")
    vault_master_key = CryptoEngine.generate_vault_master_key()
    vault_key_hex = vault_master_key.hex()
    
    print(f"[OK] vault_master_key generada: {vault_key_hex[:32]}...")
    print(f"     Tamaño: {len(vault_master_key)} bytes")
    
    # ========================================
    # PASO 2: Configurar usuarios de prueba
    # ========================================
    print("\n[PASO 2] Configurando usuarios de prueba...")
    
    users = [
        {
            "username": "RODOLFO",
            "password": "RODOLFO",  # Password real
            "user_id": 1,
            "salt_hex": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"  # 16 bytes
        },
        {
            "username": "KIKI",
            "password": "12345678",  # Password real
            "user_id": 15,  # ID correcto en Supabase
            "salt_hex": "f1e2d3c4b5a69788695847463524231a"  # 16 bytes
        }
    ]
    
    print(f"[OK] Configurados {len(users)} usuarios")
    
    # ========================================
    # PASO 3: Generar wrapped_keys
    # ========================================
    print("\n[PASO 3] Generando wrapped_master_keys...")
    
    wrapped_keys = []
    for user in users:
        username = user["username"]
        password = user["password"]
        salt = bytes.fromhex(user["salt_hex"])
        
        # Wrap vault_master_key con password del usuario
        wrapped_key = CryptoEngine.wrap_vault_key(vault_master_key, password, salt)
        wrapped_key_hex = wrapped_key.hex()
        
        wrapped_keys.append({
            "user_id": user["user_id"],
            "username": username,
            "wrapped_key_hex": wrapped_key_hex
        })
        
        print(f"[OK] {username}: wrapped_key generada ({len(wrapped_key)} bytes)")
    
    # ========================================
    # PASO 4: Verificar que funciona
    # ========================================
    print("\n[PASO 4] Verificando unwrap...")
    
    for i, user in enumerate(users):
        wrapped_hex = wrapped_keys[i]["wrapped_key_hex"]
        wrapped_bytes = bytes.fromhex(wrapped_hex)
        salt = bytes.fromhex(user["salt_hex"])
        
        try:
            unwrapped = CryptoEngine.unwrap_vault_key(wrapped_bytes, user["password"], salt)
            
            if unwrapped == vault_master_key:
                print(f"[OK] {user['username']}: Unwrap exitoso - llave coincide")
            else:
                print(f"[FAIL] {user['username']}: Llave NO coincide!")
                
        except Exception as e:
            print(f"[FAIL] {user['username']}: Error - {e}")
    
    # ========================================
    # PASO 5: Generar SQL
    # ========================================
    print("\n[PASO 5] Generando SQL...")
    
    sql_output = f"""-- ============================================================================
-- SCRIPT DE CREACIÓN DE BÓVEDA DE PRUEBA
-- ============================================================================
-- Generado automáticamente - NO editar manualmente
-- Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ============================================================================

-- PASO 1: Crear bóveda de prueba "A"
-- ============================================================================

INSERT INTO vault_groups (vault_name, vault_master_key, max_users)
VALUES (
    'A',  -- Nombre de la bóveda
    '\\\\x{vault_key_hex}',  -- vault_master_key (32 bytes)
    5  -- Máximo de usuarios
)
ON CONFLICT (vault_name) DO UPDATE 
SET vault_master_key = EXCLUDED.vault_master_key;

-- Obtener el ID de la bóveda recién creada
DO $$ 
DECLARE
    v_vault_id INTEGER;
BEGIN
    SELECT id INTO v_vault_id FROM vault_groups WHERE vault_name = 'A';
    RAISE NOTICE 'Vault ID de bóveda A: %', v_vault_id;
END $$;


-- PASO 2: Crear registros en vault_access
-- ============================================================================

"""
    
    for wrapped in wrapped_keys:
        sql_output += f"""
-- Usuario: {wrapped['username']}
INSERT INTO vault_access (user_id, vault_id, wrapped_master_key)
VALUES (
    {wrapped['user_id']},  -- user_id de {wrapped['username']}
    (SELECT id FROM vault_groups WHERE vault_name = 'A'),  -- vault_id
    '\\\\x{wrapped['wrapped_key_hex']}'  -- wrapped_master_key
)
ON CONFLICT (user_id, vault_id) DO UPDATE
SET wrapped_master_key = EXCLUDED.wrapped_master_key;
"""
    
    sql_output += """

-- PASO 3: Actualizar tabla users con vault_id
-- ============================================================================

"""
    
    for user in users:
        sql_output += f"""
UPDATE users 
SET vault_id = (SELECT id FROM vault_groups WHERE vault_name = 'A')
WHERE id = {user['user_id']};  -- {user['username']}
"""
    
    sql_output += """

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Ver bóveda creada
SELECT * FROM vault_groups WHERE vault_name = 'A';

-- Ver accesos
SELECT va.id, va.user_id, u.username, va.vault_id, vg.vault_name
FROM vault_access va
JOIN users u ON va.user_id = u.id
JOIN vault_groups vg ON va.vault_id = vg.id
WHERE vg.vault_name = 'A';

-- Ver usuarios asignados
SELECT id, username, vault_id
FROM users
WHERE vault_id = (SELECT id FROM vault_groups WHERE vault_name = 'A');

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
"""
    
    # Guardar SQL
    sql_filename = "scripts/create_test_vault.sql"
    with open(sql_filename, "w", encoding="utf-8") as f:
        f.write(sql_output)
    
    print(f"[OK] SQL generado: {sql_filename}")
    
    # ========================================
    # PASO 6: Generar archivo de configuración
    # ========================================
    config_output = f"""# CONFIGURACIÓN DE BÓVEDA DE PRUEBA
# ===================================

VAULT_NAME: A
VAULT_ID: (se asigna automáticamente en Supabase)
VAULT_MASTER_KEY: {vault_key_hex}

USUARIOS:
"""
    
    for i, user in enumerate(users):
        config_output += f"""
  - Username: {user['username']}
    User ID: {user['user_id']}
    Password (prueba): {user['password']}
    Salt: {user['salt_hex']}
    Wrapped Key: {wrapped_keys[i]['wrapped_key_hex']}
"""
    
    config_filename = ".gemini/test_vault_config.txt"
    with open(config_filename, "w", encoding="utf-8") as f:
        f.write(config_output)
    
    print(f"[OK] Configuración guardada: {config_filename}")
    
    # ========================================
    # RESUMEN FINAL
    # ========================================
    print("\n" + "="*70)
    print(" GENERACIÓN COMPLETADA")
    print("="*70)
    print(f"""
ARCHIVOS GENERADOS:
  1. {sql_filename}
  2. {config_filename}

PRÓXIMOS PASOS:
  1. Editar {sql_filename}:
     - Verificar user_id de RODOLFO y KIKI
     - Actualizar passwords si es necesario
  
  2. Ejecutar SQL en Supabase:
     - Abrir Supabase Dashboard
     - SQL Editor
     - Pegar y ejecutar el contenido de {sql_filename}
  
  3. Verificar en Supabase:
     - SELECT * FROM vault_groups WHERE vault_name = 'A';
     - SELECT * FROM vault_access;
  
  4. Probar en PassGuardian:
     - Login con RODOLFO
     - Login con KIKI
     - Ambos deben compartir la misma vault_master_key

IMPORTANTE:
  - ACTUALIZA las passwords en el SQL antes de ejecutar
  - VERIFICA los user_id correctos en Supabase
  - GUARDA el vault_master_key hex por seguridad
""")
    print("="*70)


if __name__ == "__main__":
    generate_test_vault()
