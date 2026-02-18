import json
import logging
import os

logger = logging.getLogger(__name__)

class MESSAGES:
    """Sistema de Mensajería de Alto Nivel para la Bóveda (Industrial & Cyber-Ops)."""
    
    LANG = "EN"  # "ES" or "EN"
    _DATA = {}

    @classmethod
    def _load_messages(cls):
        """Carga los mensajes desde los archivos JSON en el directorio i18n."""
        base_path = os.path.dirname(__file__)
        i18n_path = os.path.join(base_path, "i18n")
        
        for lang in ["ES", "EN"]:
            file_path = os.path.join(i18n_path, f"messages_{lang.lower()}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        cls._DATA[lang] = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading messages for {lang}: {e}")
            else:
                logger.warning(f"Message file not found: {file_path}")

    @classmethod
    def get(cls, section, key):
        """Recupera el mensaje en el idioma actual."""
        if not cls._DATA:
            cls._load_messages()
            
        try:
            return cls._DATA[cls.LANG][section][key]
        except:
            return f"[{section}.{key}]"

    # Propiedades estáticas para mantener compatibilidad con el código actual
    class CompatibilityLayer:
        def __init__(self, section):
            self.section = section
            
        def __getattr__(self, key):
            return MESSAGES.get(self.section, key)
            
        def get(self, key, default=None):
            """Permite acceso tipo diccionario con valor por defecto."""
            if not MESSAGES._DATA:
                MESSAGES._load_messages()
            try:
                return MESSAGES._DATA[MESSAGES.LANG][self.section][key]
            except:
                return default if default is not None else f"[{self.section}.{key}]"

    COMMON = CompatibilityLayer("COMMON")
    LOGIN = CompatibilityLayer("LOGIN")
    DASHBOARD = CompatibilityLayer("DASHBOARD")
    USERS = CompatibilityLayer("USERS")
    VAULT = CompatibilityLayer("VAULT")
    SECURITY = CompatibilityLayer("SECURITY")
    AI = CompatibilityLayer("AI")
    TWOFACTOR = CompatibilityLayer("TWOFACTOR")
    SETTINGS = CompatibilityLayer("SETTINGS")
    SESSIONS = CompatibilityLayer("SESSIONS")
    WIZARD = CompatibilityLayer("WIZARD")
    RECOVERY = CompatibilityLayer("RECOVERY")
    ADMIN = CompatibilityLayer("ADMIN")
    SERVICE = CompatibilityLayer("SERVICE")
    SHADOW = CompatibilityLayer("SHADOW")
    TACTICAL = CompatibilityLayer("TACTICAL")
    REPAIR = CompatibilityLayer("REPAIR")
    CARDS = CompatibilityLayer("CARDS")
    LISTS = CompatibilityLayer("LISTS")
    EXPLANATIONS = CompatibilityLayer("EXPLANATIONS")
    QUICK_ACTIONS = CompatibilityLayer("QUICK_ACTIONS")
    INFO_TILES = CompatibilityLayer("INFO_TILES")

# Inicializar carga al importar si es necesario, 
# o dejar que se cargue perezosamente en el primer get()
