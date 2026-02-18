# -*- coding: utf-8 -*-
"""
RESET COMPLETO: Eliminar ARGON2_TEST y todos sus datos
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import os

def reset_argon2_test():
    """Eliminar completamente ARGON2_TEST de Supabase y archivos locales"""
    
    print("\n" + "="*60)
    print("RESET COMPLETO: Eliminando ARGON2_TEST")
    print("="*60)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get ARGON2_TEST user
        print("\n[STEP 1] Buscando usuario ARGON2_TEST...")
        user_result = supabase.table("users").select("*").eq("username", "ARGON2_TEST").execute()
        
        if not user_result.data:
            print("[INFO] Usuario ARGON2_TEST no existe en Supabase")
        else:
            user = user_result.data[0]
            user_id = user['id']
            vault_id = user['vault_id']
            
            print(f"[OK] Usuario encontrado: {user_id}")
            print(f"[OK] Vault ID: {vault_id}")
            
            # Delete secrets created by ARGON2_TEST
            print("\n[STEP 2] Eliminando secretos de ARGON2_TEST...")
            secrets_result = supabase.table("secrets").select("id").eq("vault_id", vault_id).execute()
            
            if secrets_result.data:
                for secret in secrets_result.data:
                    supabase.table("secrets").delete().eq("id", secret['id']).execute()
                print(f"[OK] {len(secrets_result.data)} secretos eliminados")
            else:
                print("[INFO] No hay secretos para eliminar")
            
            # Delete vault_access entries
            print("\n[STEP 3] Eliminando entradas de vault_access...")
            supabase.table("vault_access").delete().eq("user_id", user_id).execute()
            print("[OK] vault_access eliminado")
            
            # Delete user
            print("\n[STEP 4] Eliminando usuario...")
            supabase.table("users").delete().eq("username", "ARGON2_TEST").execute()
            print("[OK] Usuario eliminado")
            
            # Delete vault if it's ARGON2_TEST's own vault
            print("\n[STEP 5] Verificando vault...")
            if vault_id == "18f18ab4-df5b-4fa0-bcd2-5fb83ff1bf4a":
                print("[INFO] Eliminando vault de ARGON2_TEST...")
                supabase.table("vaults").delete().eq("id", vault_id).execute()
                print("[OK] Vault eliminado")
            else:
                print("[INFO] Vault compartido, no se elimina")
        
        # Delete local database
        print("\n[STEP 6] Eliminando base de datos local...")
        local_db = "C:\\PassGuardian_v2\\data\\vault_argon2_test.db"
        if os.path.exists(local_db):
            os.remove(local_db)
            print(f"[OK] {local_db} eliminado")
        else:
            print("[INFO] No existe base de datos local")
        
        print("\n" + "="*60)
        print("[SUCCESS] RESET COMPLETO")
        print("="*60)
        print("\nTodo limpio:")
        print("  - Usuario ARGON2_TEST eliminado de Supabase")
        print("  - Secretos eliminados")
        print("  - vault_access eliminado")
        print("  - Vault eliminado (si era propio)")
        print("  - Base de datos local eliminada")
        print("\nSistema listo para empezar de cero.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    confirm = input("\n¿Estás seguro de eliminar TODO de ARGON2_TEST? (yes/no): ")
    if confirm.lower() == 'yes':
        success = reset_argon2_test()
        sys.exit(0 if success else 1)
    else:
        print("Operación cancelada")
        sys.exit(0)
