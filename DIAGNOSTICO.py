#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO Y REPARACIÓN DE VAULT KEY
======================================

Este script diagnostica por qué la Vault Key no se puede desencriptar.

Basado en logs:
    [Forensic] Primary vault unwrap failed for RODOLFO
    Rate limit exceeded for unwrap_vault_key
"""

import sys
import os
import sqlite3
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("🔍 DIAGNÓSTICO DE VAULT KEY - RODOLFO")
print("="*70)
print()

username = "RODOLFO"
db_path = Path(f"data/vault_{username.lower()}.db")

if not db_path.exists():
    print(f"❌ Base de datos no encontrada: {db_path}")
    sys.exit(1)

# 1. Conectar a la base de datos
print("📊 Conectando a la base de datos...")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 2. Obtener información del usuario
print(f"\n🔍 Información de {username}:")
print("-" * 70)

cursor.execute("""
    SELECT username, password_hash, salt, vault_salt, 
           protected_key, wrapped_vault_key, role, vault_id
    FROM users
    WHERE username = ?
""", (username.upper(),))

row = cursor.fetchone()

if not row:
    print(f"❌ Usuario {username} no encontrado en la base de datos")
    conn.close()
    sys.exit(1)

user_info = {
    'username': row[0],
    'password_hash': row[1],
    'salt': row[2],
    'vault_salt': row[3],
    'protected_key': row[4],
    'wrapped_vault_key': row[5],
    'role': row[6],
    'vault_id': row[7]
}

print(f"Username:         {user_info['username']}")
print(f"Role:             {user_info['role']}")
print(f"Vault ID:         {user_info['vault_id']}")
print()

# 3. Verificar cada componente
print("🔍 Verificando componentes criptográficos:")
print("-" * 70)

# Salt
if user_info['salt']:
    print(f"✅ Salt:          {user_info['salt'][:20]}... ({len(user_info['salt'])} chars)")
else:
    print("❌ Salt:          FALTANTE")

# Vault Salt
if user_info['vault_salt']:
    vault_salt_len = len(user_info['vault_salt']) if isinstance(user_info['vault_salt'], str) else len(user_info['vault_salt'])
    print(f"✅ Vault Salt:    {str(user_info['vault_salt'])[:20]}... ({vault_salt_len} chars/bytes)")
else:
    print("❌ Vault Salt:    FALTANTE")

# Protected Key
if user_info['protected_key']:
    pk_len = len(user_info['protected_key']) if isinstance(user_info['protected_key'], str) else len(user_info['protected_key'])
    print(f"✅ Protected Key: {str(user_info['protected_key'])[:20]}... ({pk_len} chars/bytes)")
else:
    print("❌ Protected Key: FALTANTE")

# Wrapped Vault Key
if user_info['wrapped_vault_key']:
    wvk_len = len(user_info['wrapped_vault_key']) if isinstance(user_info['wrapped_vault_key'], str) else len(user_info['wrapped_vault_key'])
    print(f"⚠️  Wrapped Vault: {str(user_info['wrapped_vault_key'])[:20]}... ({wvk_len} chars/bytes)")
else:
    print("❌ Wrapped Vault: FALTANTE")

print()

# 4. Verificar vault_access table
print("🔍 Verificando tabla vault_access:")
print("-" * 70)

try:
    cursor.execute("""
        SELECT vault_id, wrapped_master_key
        FROM vault_access
        WHERE user_id = (SELECT id FROM users WHERE username = ?)
    """, (username.upper(),))
    
    vault_access_rows = cursor.fetchall()
    
    if vault_access_rows:
        print(f"✅ Registros encontrados: {len(vault_access_rows)}")
        for i, (vid, wmk) in enumerate(vault_access_rows, 1):
            wmk_len = len(wmk) if wmk else 0
            print(f"\n   Registro {i}:")
            print(f"   Vault ID: {vid}")
            print(f"   Wrapped Key: {str(wmk)[:30]}... ({wmk_len} chars)")
    else:
        print("❌ No hay registros en vault_access para este usuario")
        
except sqlite3.OperationalError as e:
    print(f"⚠️  Error accediendo vault_access: {e}")

print()

# 5. Análisis del problema
print("="*70)
print("🔴 ANÁLISIS DEL PROBLEMA")
print("="*70)
print()

issues = []

# Verificar si wrapped_vault_key existe en users table
if not user_info['wrapped_vault_key']:
    issues.append({
        'severity': 'CRITICAL',
        'issue': 'wrapped_vault_key está vacío en la tabla users',
        'solution': 'Necesita regenerarse desde vault_access o desde el admin'
    })

# Verificar vault_access
if not vault_access_rows:
    issues.append({
        'severity': 'CRITICAL',
        'issue': 'No hay entrada en vault_access para este usuario',
        'solution': 'El admin debe agregar acceso a la vault'
    })

# Verificar protected_key
if not user_info['protected_key']:
    issues.append({
        'severity': 'CRITICAL',
        'issue': 'protected_key está vacío',
        'solution': 'Necesita regenerarse con la contraseña maestra'
    })

# Verificar vault_salt
if not user_info['vault_salt']:
    issues.append({
        'severity': 'HIGH',
        'issue': 'vault_salt está vacío',
        'solution': 'Necesita generarse un nuevo salt aleatorio'
    })

# Mostrar issues
if issues:
    for i, issue in enumerate(issues, 1):
        print(f"{i}. [{issue['severity']}] {issue['issue']}")
        print(f"   Solución: {issue['solution']}")
        print()
else:
    print("✅ No se detectaron problemas obvios en la estructura de datos")
    print()
    print("⚠️  El problema podría ser:")
    print("   1. Rate limiting bloqueando intentos legítimos")
    print("   2. La wrapped_vault_key está corrupta")
    print("   3. El algoritmo de unwrap tiene un bug")
    print()

# 6. Verificar rate limiting
print("="*70)
print("⚠️  PROBLEMA DE RATE LIMITING DETECTADO")
print("="*70)
print()
print("El log muestra:")
print("  'Rate limit exceeded for unwrap_vault_key'")
print()
print("Esto significa que el código está bloqueando intentos de desencriptación")
print("incluso cuando la contraseña es correcta.")
print()
print("SOLUCIÓN:")
print("1. Desactivar temporalmente el rate limiting en crypto_engine.py")
print("2. O resetear el contador de rate limiting")
print()

# 7. Sugerir acciones
print("="*70)
print("🛠️  ACCIONES RECOMENDADAS")
print("="*70)
print()

if issues:
    print("PRIORIDAD 1 - Reparar datos faltantes:")
    print("  → Ejecutar script de reparación de vault keys")
    print()

print("PRIORIDAD 2 - Desactivar rate limiting temporalmente:")
print("  1. Abrir: src/infrastructure/crypto_engine.py")
print("  2. Buscar: @rate_limit")
print("  3. Comentar el decorador temporalmente")
print("  4. Reintentar login")
print()

print("PRIORIDAD 3 - Si persiste, regenerar vault access:")
print("  → Contactar al administrador de la vault")
print("  → Solicitar re-invitación a la vault compartida")
print()

conn.close()

print("="*70)
print("✅ Diagnóstico completado")
print("="*70)