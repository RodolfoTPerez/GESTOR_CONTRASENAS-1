import sqlite3
import os
from pathlib import Path

# Mocking SecurityService-like decryption to check state
def analyze_policy_enforcement():
    conn = sqlite3.connect("data/vault_rodolfo.db")
    conn.row_factory = sqlite3.Row
    secrets = conn.execute("SELECT id, service, owner_name, is_private FROM secrets").fetchall()
    
    print("--- Database Policy Audit ---")
    print(f"{'ID':<4} | {'Service':<15} | {'Owner':<10} | {'Private':<8} | {'Status'}")
    print("-" * 60)
    
    for s in secrets:
        is_private = s['is_private']
        owner = s['owner_name']
        
        # Policy Check logic
        if is_private == 0:
            intended = "PUBLIC (Shared)"
        else:
            intended = f"PRIVATE ({owner})"
            
        print(f"{s['id']:<4} | {s['service']:<15} | {owner:<10} | {is_private:<8} | {intended}")

    conn.close()

if __name__ == "__main__":
    analyze_policy_enforcement()
