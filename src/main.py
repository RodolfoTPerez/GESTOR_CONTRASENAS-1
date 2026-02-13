import sys
import os
import logging

# Silencia advertencias de Qt en la consola
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false"

# Add project root to sys.path so we can import 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt5.QtWidgets import QApplication
from src.presentation.login_view import LoginView
# OPTIMIZACIÓN: DashboardView se importa lazy (dentro de on_login_success) para no frenar el arranque.
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.sync_manager import SyncManager
from src.infrastructure.user_manager import UserManager
from src.presentation.ui_utils import PremiumMessage
from src.domain.messages import MESSAGES
from config.config import SUPABASE_URL, SUPABASE_KEY
# Configuración de logging profesional
from src.infrastructure.config.path_manager import PathManager
data_dir = PathManager.DATA_DIR
data_dir.mkdir(exist_ok=True)
log_file = data_dir / "debug.log"

LOG_LEVEL = os.getenv("PG_LOG_LEVEL", "INFO").upper()

# Formato: 2026-02-06 23:56:20 INFO [module_name] Message
log_format = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=LOG_LEVEL,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.StreamHandler(), # Consola
        logging.FileHandler(log_file, encoding='utf-8') # Archivo
    ]
)

logger = logging.getLogger("Main")

# Silenciar ruido de librerías HTTP
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def start_app():
    # --- FIX SENIOR: Habilitar escalado de alta densidad para evitar borrosidad en QRs ---
    from PyQt5.QtCore import Qt, QCoreApplication
    from src.presentation.theme_manager import ThemeManager
    from PyQt5.QtCore import QSettings

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    QCoreApplication.setOrganizationName(ThemeManager.APP_ID)
    QCoreApplication.setApplicationName("VultraxCore_Global")
    
    app = QApplication(sys.argv)
    
    tm = ThemeManager()
    
    # --- [SENIOR] CARGA DE CONFIGURACIÓN GLOBAL (INI para máxima fiabilidad) ---
    config_path = str(PathManager.GLOBAL_SETTINGS_INI)
    global_settings = QSettings(config_path, QSettings.IniFormat)
    
    # 1. Aplicar Tema Global
    active_theme = global_settings.value("theme_active", "tactical_dark")
    tm.set_theme(active_theme)
    tm.apply_app_theme(app)
    logger.info(f"Tema Global: {active_theme} | Fuente: {config_path}")

    # 1. Iniciamos el SecretsManager (Maneja la DB SQLite)
    sm = SecretsManager(None)
    # 2. Iniciamos el UserManager con referencia a la DB local
    um = UserManager(sm)

    # --- DETECCIÓN DE ESTADO CERO (INSTALACIÓN) ---
    local_users_exist = False
    try:
        vault_dbs = list(data_dir.glob("vault_*.db"))
        local_users_exist = len(vault_dbs) > 0
        logger.info(f"Bases de datos encontradas: {len(vault_dbs)}")
        if vault_dbs:
            logger.info(f"Archivos vault_*.db: {[db.name for db in vault_dbs]}")
    except Exception as e:
        logger.error(f"Error verificando usuarios locales: {e}")
        local_users_exist = False
    
    if not local_users_exist:
        from src.presentation.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(sm, um)
        if wizard.exec_() != 1:
            sys.exit(0)
    
    # 2. Cargar Idioma Global (Prioridad Absoluta)
    saved_lang = global_settings.value("language")
    
    # Fallback a meta si no hay settings (compatibilidad legacy)
    if not saved_lang or saved_lang not in ["ES", "EN"]:
        saved_lang = sm.get_meta("language")
        
    if saved_lang and saved_lang in ["ES", "EN"]:
        MESSAGES.LANG = saved_lang
        logger.info(f"Idioma Global cargado: {MESSAGES.LANG}")
    else:
        # Default fallback
        MESSAGES.LANG = "EN"
        logger.info("Idioma por defecto (EN) aplicado.")

    # 3. Creamos el login pasando el UserManager
    login_window = LoginView(um)
    app.login_window = login_window  # Mantener referencia
    app.dashboard = None

    def on_login_success(master_password, totp_secret, user_profile):
        logger.info(f"[DEBUG] on_login_success entered for {user_profile.get('username')}")
        try:
            # Sincronización de perfil: Ahora es segura gracias al blindaje de preservación local
            logger.info("[DEBUG] Syncing user to local...")
            um.sync_user_to_local(user_profile['username'], user_profile)
            
            # 1. Activar usuario (esto cambia la conexión a vault_<user>.db)
            logger.info("[DEBUG] Activating user session...")
            sm.set_active_user(user_profile['username'], master_password)
            
            # 2. Asegurar que el contexto de Bóveda (Vault ID) esté activo
            if user_profile.get('vault_id'):
                sm.current_vault_id = user_profile['vault_id']
                logger.info(f"Contexto de Bóveda establecido: {sm.current_vault_id}")
            
            logger.info("[DEBUG] Creating SyncManager...")
            sync = SyncManager(sm, SUPABASE_URL, SUPABASE_KEY)
            
            # LAZY LOADING: Importar Dashboard aquí ahorra 3-4 segundos de inicio
            logger.info("[DEBUG] Lazy loading DashboardView...")
            from src.presentation.dashboard.dashboard_view import DashboardView
            
            logger.info("[DEBUG] Instantiating DashboardView...")
            dashboard = DashboardView(sm, sync, um, user_profile)
            app.dashboard = dashboard  # Mantener referencia global
            logger.info("[DEBUG] Showing Dashboard...")
            dashboard.show()
            dashboard.raise_()
            dashboard.activateWindow()
            login_window.close()
            logger.info("[DEBUG] Login flow completed successfully.")
        except ValueError as ve:
            # Error de negocio/lógica (como el cambio de Master Key)
            logger.warning(f"Vault Integrity Warning: {ve}")
            PremiumMessage.warning(None, MESSAGES.VAULT.TITLE_SECURITY, str(ve))
            # Continuamos cargando, es solo un aviso de integridad
            
        except Exception as e:
            logger.critical(f"Critical Startup Error: {e}")
            # Diagnóstico extendido para facilitar soporte
            logger.critical(f"User Context: {user_profile.get('username', 'Unknown')}")
            logger.critical(f"Vault Context: {user_profile.get('vault_id', 'Unknown')}")
            logger.critical("Stack trace:", exc_info=True)
            
            PremiumMessage.critical(
                None, 
                MESSAGES.VAULT.TITLE_CRITICAL, 
                f"{str(e)}\n\nSi el error persiste, contacte a soporte con el log 'debug.log'."
            )
            sys.exit(1)

    login_window.on_login_success = on_login_success
    login_window.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    start_app()
