import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.secrets_manager import SecretsManager

sm = SecretsManager()
sm.set_active_user("RODOLFO", "RODOLFO")

print(f"--- Decrypting records for {sm.current_user} ---")
records = sm.get_all()
for r in records:
    print(f"ID: {r['id']} | Service: {r['service']} | Secret: {r['secret']}")

count_locked = sum(1 for r in records if r['secret'] == "[Bloqueado 🔑]")
print(f"\nTotal: {len(records)} | Locked: {count_locked}")
