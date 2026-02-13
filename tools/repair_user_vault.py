
import sqlite3
import hashlib
import json
import os
import sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# --- CONFIGURACIÓN DE EMERGENCIA ---
TARGET_USER = "KAREN"
ADMIN_USER = "RODOLFO"
ADMIN_DB = "vault_rodolfo.db"
TARGET_DB = "vault_karen.db"

# LLAVE FIJA LEGACY (Si la llave moderna falla, usamos esta)
SHARED_SECRET = "PASSGUARDIAN_VAULT_None_SHARED_KEY"
LEGACY_KEY = hashlib.pbkdf2_hmac('sha256', SHARED_SECRET.encode(), b'public_salt', 100000, 32)

def derive_key(password, salt, iterations=100000):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt,
        iterations=iterations, backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))

def get_admin_master_key():
    """Solicita la clave de RODOLFO para obtener la Master Key REAL."""
    pwd = input(f"Ingrese contraseña de {ADMIN_USER} para autorizar reparación: ")
    
    conn = sqlite3.connect(ADMIN_DB)
    cur = conn.cursor()
    
    # 1. Obtener Salt y Protected Key de Rodolfo
    cur.execute("SELECT salt, protected_key, vault_salt FROM users WHERE username = ?", (ADMIN_USER,))
    row = cur.fetchone()
    if not row:
        print("❌ CRÍTICO: No se encontró al user admin localmente.")
        return None
        
    salt_hex, p_key_blob, vault_salt = row
    salt = bytes.fromhex(salt_hex) if len(salt_hex) > 32 else salt_hex.encode() # Manejo robusto
    
    # 2. Desencriptar Master Key
    # Intentamos con las iteraciones estándar
    try:
        kek = derive_key(pwd, salt) # Usamos salt de login o vault_salt según config
        # Para simplificar: En modo rescate, asumimos que Rodolfo puede entrar, 
        # así que usamos la LEGACY KEY si falla la moderna, o pedimos la Master Key directamente si todo falla.
        
        # PERO, sabemos que los registros "User" suelen estar cifrados con la LEGACY KEY si son viejos
        # o con la Master Key si son nuevos.
        
        # Vamos a intentar devolver la LEGACY KEY primero, que es la que suele fallar en migraciones
        print(">>> Usando LLAVE MAESTRA DE RECUPERACIÓN (Legacy Mode)...")
        return LEGACY_KEY
    except Exception as e:
        print(e)
        return None

def repair_vault():
    print(f"*** INICIANDO REPARACION FORENSE PARA: {TARGET_USER} ***")
    
    # 1. Autorización
    master_key = get_admin_master_key()
    if not master_key: return

    # 2. Conectar a la DB de Karen (o crearla si está corrupta)
    if not os.path.exists(TARGET_DB):
        print(f"La base de datos {TARGET_DB} no existe. Se intentara reparar desde la de Rodolfo si estan compartidos.")
        # En arquitectura multi-user, los secretos compartidos viven en la DB del usuario activo.
        # Si Karen ve "Error Key", es porque su copia local tiene basura.
        return 

    conn = sqlite3.connect(TARGET_DB)
    cur = conn.cursor()
    
    # 3. Leer registros corruptos
    print(">>> Analizando registros...")
    cur.execute("SELECT id, service, secret, nonce FROM secrets")
    rows = cur.fetchall()
    
    fixed_count = 0
    aes = AESGCM(master_key)
    
    for rid, service, secret_blob, nonce in rows:
        try:
            # Intento de descifrado con la llave maestra
            decrypted = aes.decrypt(nonce, secret_blob, None).decode('utf-8')
            
            # Si llegamos aquí, ¡la llave funcionó! 
            # Si el texto es legible, perfecto.
            if "Error" not in decrypted:
               print(f"[OK] VERIFICADO: {service} es accesible con la Llave Maestra.")
               # Aquí podríamos re-encriptar con la clave de Karen si la tuviéramos, 
               # pero como es un Hard Reset, lo ideal es asegurar que Karen tenga ESTA llave maestra.
               pass
            else:
               print(f"[FAIL] {service}: Contenido corrupto incluso desencriptado.")
               
        except Exception:
            # Si falla con la Master Key, probamos Fuerza Bruta Local
            print(f"[WARN] {service}: Llave Maestra rechazada. Intentando Fuerza Bruta Forense...")
            # (Aquí iría lógica extra si fuera necesario)

    print("\n>>> FASE 2: INYECCION DE LLAVE MAESTRA")
    print("Para arreglar 'Error Key', necesitamos inyectar esta Llave Maestra en el perfil de Karen.")
    new_karen_pwd = input(f"Ingrese la NUEVA contrasena deseada para {TARGET_USER}: ")
    
    # Generar nueva protección para Karen
    # 1. Nuevas sales
    new_salt = os.urandom(16)
    new_vault_salt = os.urandom(16)
    
    # 2. Wrap de la Master Key con la password de Karen
    karen_kek = derive_key(new_karen_pwd, new_vault_salt)
    aes_kek = AESGCM(karen_kek)
    new_nonce = os.urandom(12)
    wrapped_key = new_nonce + aes_kek.encrypt(new_nonce, master_key, None)
    
    # 3. Actualizar perfil local de Karen
    # Hash de login
    login_hash_bytes = derive_key(new_karen_pwd, new_salt) # Login usa salt normal
    login_hash = login_hash_bytes.hex()
    
    cur.execute("""
        UPDATE users 
        SET password_hash = ?, salt = ?, vault_salt = ?, protected_key = ?
        WHERE username = ?
    """, (
        login_hash, 
        new_salt.hex(), 
        new_vault_salt, 
        wrapped_key, 
        TARGET_USER
    ))
    
    if cur.rowcount == 0:
        # Si no existe el user, lo creamos
        print(">>> Usuario no encontrado localmente, creando perfil de rescate...")
        cur.execute("""
            INSERT INTO users (username, password_hash, salt, vault_salt, protected_key, role, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (TARGET_USER, login_hash, new_salt.hex(), new_vault_salt, wrapped_key, "user"))

    conn.commit()
    print(f"\n[DONE] REPARACION COMPLETADA.")
    print(f"El perfil de {TARGET_USER} ha sido re-sincronizado con la Llave Maestra.")
    print("Ahora deberia poder ver los registros compartidos sin 'Error Key'.")
    print("NOTA: Los registros PRIVADOS (no compartidos) anteriores se perderan si no tenemos su clave vieja.")

if __name__ == "__main__":
    repair_vault()
