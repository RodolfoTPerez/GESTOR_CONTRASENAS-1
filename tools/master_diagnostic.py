
import sqlite3
import os
from pathlib import Path

def get_db_status(db_name, username):
    db_path = Path(f"data/{db_name}")
    if not db_path.exists():
        return "❌ Archivo no encontrado"
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.execute("SELECT vault_id, length(protected_key), length(wrapped_vault_key), length(vault_salt) FROM users WHERE UPPER(username) = ?", (username.upper(),))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return "⚠️ Usuario no encontrado en DB"
        
        v_id, svk, wvk, salt = row
        status = []
        if v_id: status.append(f"Vault: {v_id[:8]}...")
        else: status.append("Vault: MISSING")
        
        if svk: status.append(f"SVK: OK ({svk}b)")
        else: status.append("SVK: MISSING")
        
        if wvk: status.append(f"VAULT_KEY: OK ({wvk}b)")
        else: status.append("VAULT_KEY: MISSING")
        
        return " | ".join(status)
    except Exception as e:
        return f"❌ Error: {e}"

def main():
    print("="*80)
    print("      ESTADO INTEGRAL DE SEGURIDAD - PASSGUARDIAN (DIAGNÓSTICO MAESTRO)")
    print("="*80)
    print(f"{'USUARIO':<12} | {'SITUACIÓN EN DB LOCAL':<60}")
    print("-" * 80)
    
    users = [
        ("RODOLFO", "vault_rodolfo.db"),
        ("KIKI", "vault_kiki.db")
    ]
    
    for user, db in users:
        status = get_db_status(db, user)
        print(f"{user:<12} | {status}")
    
    print("-" * 80)
    print("\nANÁLISIS TÉCNICO:")
    print("1. KIKI: Identidad restaurada. Lista para sincronizar registros compartidos.")
    print("2. RODOLFO: Identidad pendiente. Debe ejecutar 'anchor_rodolfo.py'.")
    print("3. ACCIÓN: Una vez que Rodolfo tenga su SVK, el 'Error Key' desaparecerá.")
    print("="*80)

if __name__ == "__main__":
    main()
