import os
from pathlib import Path

class PathManager:
    """
    Centralized path management for PassGuardian.
    Ensures portability by resolving paths relative to the project root.
    """
    import sys
    
    # Resolucion de Base Dir para compatibilidad con PyInstaller (.exe)
    if getattr(sys, 'frozen', False):
        # Carpeta temporal donde PyInstaller extrae los datos
        BUNDLE_DIR = Path(sys._MEIPASS)
        # Carpeta real donde reside el .exe (para persistencia de DBs)
        BASE_DIR = Path(sys.executable).parent
    else:
        BUNDLE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        BASE_DIR = BUNDLE_DIR
    
    # Data directory (Persistent)
    DATA_DIR = BASE_DIR / "data"
    
    # Assets directory (Bundled - can be BUNDLE_DIR if we include them)
    ASSETS_DIR = BUNDLE_DIR / "assets"
    
    # Config directory
    CONFIG_DIR = BASE_DIR / "config"
    
    # Path to the primary .env file (Persistent or BUNDLED?)
    # Usualmente .env debería ser persistente si el usuario quiere editarlo,
    # pero para el primer EXE lo buscamos en el BUNDLE si lo empaquetamos.
    ENV_FILE = BASE_DIR / ".env"
    if not ENV_FILE.exists() and getattr(sys, 'frozen', False):
        ENV_FILE = BUNDLE_DIR / ".env"
    
    # Primary databases and configs
    GLOBAL_DB = DATA_DIR / "vultrax.db"
    GLOBAL_SETTINGS_INI = DATA_DIR / "global_settings.ini"
    
    @classmethod
    def get_user_db(cls, username: str) -> Path:
        """Returns the path to a specific user's vault database."""
        safe_name = "".join(x for x in username.lower() if x.isalnum())
        return cls.DATA_DIR / f"vault_{safe_name}.db"

    @classmethod
    def ensure_dirs(cls):
        """Creates necessary directories if they don't exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Self-initialize directories on import
PathManager.ensure_dirs()
