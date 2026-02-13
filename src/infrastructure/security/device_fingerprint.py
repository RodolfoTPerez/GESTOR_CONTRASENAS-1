import subprocess
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

def get_hwid():
    """
    Genera un ID único basado en el hardware físico de la PC (Windows).
    Combina el Serial de la Placa Base y el UUID del Sistema.
    """
    try:
        # 1. Obtener Serial de la Placa Base (Motherboard)
        cmd_mb = "wmic baseboard get serialnumber"
        serial_mb = subprocess.check_output(cmd_mb, shell=True).decode().split('\n')[1].strip()
        
        # 2. Obtener UUID del Sistema
        cmd_uuid = "wmic csproduct get uuid"
        uuid_sys = subprocess.check_output(cmd_uuid, shell=True).decode().split('\n')[1].strip()
        
        # Combinar y crear un hash robusto (SHA-256)
        raw_id = f"PG-BIND-{serial_mb}-{uuid_sys}"
        hwid = hashlib.sha256(raw_id.encode()).hexdigest().upper()
        
        return hwid
    except Exception as e:
        # Fallback en caso de error (menos seguro, pero evita que la app truene)
        import uuid
        node = uuid.getnode()
        return hashlib.sha256(f"FALLBACK-{node}".encode()).hexdigest().upper()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("="*50)
    logger.info("VULTRAX CORE - DEVICE IDENTIFIER")
    logger.info("="*50)
    my_id = get_hwid()
    logger.info(f"YOUR DIGITAL FINGERPRINT (HWID): {my_id}")
    logger.info("This ID will be linked to your account in Supabase.")
    logger.info("="*50)
