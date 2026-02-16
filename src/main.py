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

def _setup_environment():
    """Configura el entorno de ejecución y escalado DPI."""
    from PyQt5.QtCore import Qt, QCoreApplication
    from src.presentation.theme_manager import ThemeManager
    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    QCoreApplication.setOrganizationName(ThemeManager.APP_ID)
    QCoreApplication.setApplicationName("VultraxCore_Global")

def _load_global_config(app, tm):
    """Carga el tema y la configuración de QSettings."""
    from PyQt5.QtCore import QSettings
    config_path = str(PathManager.GLOBAL_SETTINGS_INI)
    global_settings = QSettings(config_path, QSettings.IniFormat)
    
    active_theme = global_settings.value("theme_active", "tactical_dark")
    tm.set_theme(active_theme)
    tm.apply_app_theme(app)
    logger.info(f"Tema Global: {active_theme} | Fuente: {config_path}")
    return global_settings

def _initialize_core_managers():
    """Inicializa los managers de identidad y secretos."""
    sm = SecretsManager(None)
    um = UserManager(sm)
    return sm, um

def _handle_first_run(sm, um):
    """Detecta si es el primer inicio y lanza el SetupWizard."""
    try:
        vault_dbs = list(data_dir.glob("vault_*.db"))
        local_users_exist = len(vault_dbs) > 0
        if not local_users_exist:
            from src.presentation.dialogs.setup_wizard import SetupWizard
            wizard = SetupWizard(sm, um)
            if wizard.exec_() != 1:
                sys.exit(0)
    except Exception as e:
        logger.error(f"Error verificando usuarios locales: {e}")

def _load_language(sm, global_settings):
    """Configura el idioma global del sistema."""
    saved_lang = global_settings.value("language")
    if not saved_lang or saved_lang not in ["ES", "EN"]:
        saved_lang = sm.get_meta("language")
        
    MESSAGES.LANG = saved_lang if saved_lang in ["ES", "EN"] else "EN"
    logger.info(f"Idioma Global cargado: {MESSAGES.LANG}")

def start_app():
    """Punto de entrada principal de la aplicación."""
    _setup_environment()
    app = QApplication(sys.argv)
    
    from src.presentation.theme_manager import ThemeManager
    tm = ThemeManager()
    
    global_settings = _load_global_config(app, tm)
    sm, um = _initialize_core_managers()
    _handle_first_run(sm, um)
    _load_language(sm, global_settings)

    # Inicializar Login
    login_window = LoginView(um)
    app.login_window = login_window
    app.dashboard = None

    def on_login_success(master_password, totp_secret, user_profile):
        _handle_login_success(app, sm, um, master_password, user_profile)

    login_window.on_login_success = on_login_success
    login_window.show()
    sys.exit(app.exec_())

def _handle_login_success(app, sm, um, master_password, user_profile):
    """Gestiona la transición exitosa del login al dashboard."""
    try:
        username = user_profile['username']
        
        # [BOOTSTRAP SYNC] Initialize SyncManager early to pull updated security keys
        sync = SyncManager(sm, SUPABASE_URL, SUPABASE_KEY)
        try:
            # Sincronizamos el perfil y las llaves de acceso ANTES de intentar el unwrap en set_active_user
            # Esto evita el error de "Blocked Key" si hubo un cambio de clave en otro dispositivo o sesión
            if user_profile.get('id'):
                sync._sync_shared_keys(cloud_user_id=user_profile['id'])
            else:
                # Fallback por si no tenemos ID
                um.sync_user_to_local(username, user_profile)
        except Exception as sync_err:
            logger.warning(f"Bootstrap Sync failed: {sync_err}. Proceeding with local keys.")
            um.sync_user_to_local(username, user_profile)

        sm.set_active_user(username, master_password)
        
        if user_profile.get('vault_id'):
            sm.current_vault_id = user_profile['vault_id']
            
        from src.presentation.dashboard.dashboard_view import DashboardView
        dashboard = DashboardView(sm, sync, um, user_profile)
        app.dashboard = dashboard
        
        dashboard.show()
        dashboard.raise_()
        dashboard.activateWindow()
        logger.info(f"Sesión iniciada correctamente para {username}")
    except Exception as e:
        _handle_critical_error(e, user_profile)

def _handle_critical_error(e, user_profile):
    """Maneja errores críticos durante el arranque de la sesión."""
    logger.critical(f"Critical Startup Error: {e}", exc_info=True)
    PremiumMessage.critical(
        None, 
        MESSAGES.VAULT.TITLE_CRITICAL, 
        f"{str(e)}\n\nSi el error persiste, contacte a soporte."
    )
    sys.exit(1)
if __name__ == "__main__":
    start_app()
