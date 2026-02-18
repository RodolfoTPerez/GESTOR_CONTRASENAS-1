# -*- coding: utf-8 -*-
"""
Test offline delete sync
"""

import sys
sys.path.insert(0, 'C:\\PassGuardian_v2')

import sqlite3

def check_deleted_records():
    """Check for records marked as deleted in local DB"""
    
    print("\n" + "="*60)
    print("Checking Deleted Records in Local DB")
    print("="*60)
    
    # Check all vault DBs
    vaults = [
        "C:\\PassGuardian_v2\\data\\vault_rodolfo.db",
        "C:\\PassGuardian_v2\\data\\vault_kiki.db",
    ]
    
    for vault_path in vaults:
        try:
            conn = sqlite3.connect(vault_path)
            cursor = conn.cursor()
            
            vault_name = vault_path.split('\\')[-1]
            print(f"\n[{vault_name}]")
            
            # Check for deleted=1 records
            deleted = cursor.execute("SELECT id, service, deleted, synced, cloud_id FROM secrets WHERE deleted=1").fetchall()
            
            if deleted:
                print(f"  Found {len(deleted)} deleted records:")
                for rec in deleted:
                    print(f"    ID:{rec[0]} Service:{rec[1]} deleted:{rec[2]} synced:{rec[3]} cloud_id:{rec[4]}")
            else:
                print("  No deleted records found")
            
            # Check for unsynced records
            unsynced = cursor.execute("SELECT id, service, deleted, synced, cloud_id FROM secrets WHERE synced=0").fetchall()
            
            if unsynced:
                print(f"  Found {len(unsynced)} unsynced records:")
                for rec in unsynced:
                    print(f"    ID:{rec[0]} Service:{rec[1]} deleted:{rec[2]} synced:{rec[3]} cloud_id:{rec[4]}")
            else:
                print("  All records synced")
            
            conn.close()
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_deleted_records()
