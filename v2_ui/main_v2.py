import sys
import os
import json
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWebChannel import QWebChannel

# Importar los componentes reales del sistema
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.sync_manager import SyncManager
from src.presentation.dashboard.dashboard_workers import ConnectivityWorker, HeuristicWorker
from src.presentation.dashboard.dashboard_sync_actions import DashboardSyncActions
from config.config import SUPABASE_URL, SUPABASE_KEY
import time

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("VultraxV2")

class CustomWebPage(QWebEnginePage):
    """Subclase para capturar logs de JS en la consola de Python"""
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        log_map = {0: "DEBUG", 1: "INFO", 2: "WARNING", 3: "ERROR"}
        lvl_name = log_map.get(level, "JS")
        print(f"[{lvl_name} (JS) - Line {lineNumber}] {message}")
        sys.stdout.flush()

from bridge_handlers import AuthHandler, VaultHandler, SystemHandler, NavigationDispatcher

class MainWindow(QMainWindow, DashboardSyncActions):
    # [SIGNAL FIX] Canal seguro para refrescar la UI desde hilos de fondo
    sync_finished = pyqtSignal()
    sync_started = pyqtSignal(str)
    sync_progress = pyqtSignal(int, str)
    sync_completed = pyqtSignal(dict)

    def __init__(self, secrets_manager, sync_manager, user_manager, user_profile):
        super().__init__()
        company = secrets_manager.get_meta("instance_name") or "PASS GUARDIAN V2"
        self.setWindowTitle(f"{company} | CORE_HUD")
        self.showMaximized()

        # 1. Motores de Seguridad (Inyectados)
        self.sm = secrets_manager
        self.um = user_manager
        self.sync_manager = sync_manager
        self.user_profile = user_profile
        self.internet_online = False
        
        # [THEME INIT] Sincronizar estética global
        from src.presentation.theme_manager import ThemeManager
        self.tm = ThemeManager(QApplication.instance())
        self.tm.apply_app_theme(QApplication.instance())
        
        logger.info(f"CORE: V2 HUD Inicializado para {user_profile.get('username')}")

        # 1.1 Iniciar Hilos de Trabajo
        self.conn_worker = ConnectivityWorker(self.sync_manager, self.sm)
        self.heur_worker = HeuristicWorker(self.sm, self.um)

        # 2. Browser y Canal
        self.browser = QWebEngineView()
        self.page = CustomWebPage(self.browser)
        self.browser.setPage(self.page)
        
        # Inyectar dependencias en los handlers
        self.auth_handler = AuthHandler(self.sm, self.um, self)
        self.vault_handler = VaultHandler(self.sm, self.sync_manager, self)
        self.system_handler = SystemHandler(self.sm)
        self.nav_handler = NavigationDispatcher(self)

        self.channel = QWebChannel()
        self.channel.registerObject("auth", self.auth_handler)
        self.channel.registerObject("vault", self.vault_handler)
        self.channel.registerObject("system", self.system_handler)
        self.channel.registerObject("api", self.nav_handler)
        self.channel.registerObject("handler", self.vault_handler) # Tactical Bridge Alias
        
        # Conectar Hilos al Bridge
        self.conn_worker.status_updated.connect(self._on_connectivity_update)
        self.heur_worker.stats_updated.connect(self.system_handler.update_stats)
        self.sync_finished.connect(self._load_table)
        
        # Modern Sync UI Connections
        self.sync_started.connect(lambda t: self._js_safe_call("openSyncModal", t))
        self.sync_progress.connect(lambda v, m: self._js_safe_call("updateSyncProgress", v, m))
        self.sync_completed.connect(lambda s: self.page.runJavaScript(f"showSyncSummary({json.dumps(s)})"))
        # Re-inject theme vars when user changes theme from within the HUD
        self.vault_handler.themeChanged.connect(lambda: self._inject_theme_vars(True))
        
        # [SECURITY ENFORCEMENT] Force password change protocol
        self.vault_handler.forcePasswordChange.connect(self._on_force_password_change)
        
        # Arrancar hilos
        self.conn_worker.start()
        self.heur_worker.start()
        
        self.page.setWebChannel(self.channel)

        # 3. Configurar Seguridad del Browser
        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)

        # 4. Cargar pantalla de Login (Punto de entrada de seguridad)
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'login.html'))
        u = QUrl.fromLocalFile(path)
        logger.info(f"UI: Cargando Punto de Acceso: {u.toString()}")
        self.browser.setUrl(u)
        
        self.setCentralWidget(self.browser)

        # [THEME BRIDGE] Inject Python theme colors into HTML on every page load
        self.browser.loadFinished.connect(self._inject_theme_vars)

    def _inject_theme_vars(self, ok):
        """THEME BRIDGE: Injects active ThemeManager palette into HTML CSS vars."""
        if not ok:
            return
        try:
            from src.presentation.theme_manager import ThemeManager
            tm = ThemeManager()
            c = tm.get_theme_colors()
            theme_id = ThemeManager._GLOBAL_THEME or "tactical_dark"

            p    = c.get("primary",   "#00f2ff")
            sec  = c.get("secondary", "#7000ff")
            bg   = c.get("bg",        "#06070a")
            bgs  = c.get("bg_sec",    "#0d1117")
            tx   = c.get("text",      "#e0e6ed")
            txd  = c.get("text_dim",  "rgba(255,255,255,0.55)")
            dng  = c.get("danger",    "#ff003c")
            wrn  = c.get("warning",   "#ffae00")
            suc  = c.get("success",   "#00ff95")
            glw  = c.get("glow",      "rgba(0,242,255,0.3)")
            cb   = c.get("card_bg",   "rgba(15,18,25,0.7)")
            brd  = c.get("border",    "rgba(0,242,255,0.2)")

            # Map to dashboard.css variables (single line, no newlines in CSS block)
            tokens = [
                f"--primary:{p}", f"--secondary:{sec}",
                f"--accent-1:{p}", f"--accent-2:{suc}",
                f"--accent-3:{wrn}", f"--accent-4:{sec}",
                f"--success:{suc}", f"--warning:{wrn}", f"--danger:{dng}",
                f"--bg-gradient:linear-gradient(135deg,{bg},{bgs},{bg})",
                f"--bg-sec:{bgs}", f"--glass-bg:{cb}",
                f"--glass-border:{brd}", f"--glass-glow:{glw}",
                f"--text-main:{tx}", f"--text-dim:{txd}",
                f"--gauge-bg:{brd}",
            ]
            css_vars = "; ".join(tokens) + ";"

            body_class = {
                "aura_forest":   "aura",
                "nebula_velvet": "nebula",
                "vultrax_v2":    "vultrax",
                "tactical_dark": "tactical",
                "bunker_ops":    "bunker",
                "cyber_arctic":  "arctic",
            }.get(theme_id, "tactical")

            # Build JS as a single-line string - NO newlines embedded, no f-string multiline
            css_content = ":root{" + css_vars + "}"
            js_parts = [
                "(function(){",
                "var s=document.getElementById('__py_theme_bridge__');",
                "if(!s){s=document.createElement('style');s.id='__py_theme_bridge__';document.head.appendChild(s);}",
                "s.textContent=" + repr(css_content) + ";",
                "document.body.className=document.body.className.replace(/(aura|nebula|vultrax|tactical|bunker|arctic)/g,'').trim();",
                f"document.body.classList.add('{body_class}');",
                "document.body.classList.add('theme-injected');",
                f"console.log('[THEME] {theme_id} -> {body_class}');",
                "})();",
            ]
            self.page.runJavaScript("".join(js_parts))
            logger.info("THEME_BRIDGE: %s -> %s OK", theme_id, body_class)
        except Exception as e:
            logger.error("THEME_BRIDGE_ERR: %s", e)


    def _js_safe_call(self, func_name, *args):
        """Helper to call JS functions with safe string escaping."""
        safe_args = []
        for a in args:
            if isinstance(a, str):
                escaped = a.replace("'", "\\'")
                safe_args.append(f"'{escaped}'")
            else:
                safe_args.append(str(a))
        js = f"{func_name}({', '.join(safe_args)})"
        self.page.runJavaScript(js)

    def _on_connectivity_update(self, internet, sup, sql, sync_err, audit_err, is_syncing):
        """Pipes connectivity status to the telemetry bridge."""
        self.internet_online = internet
        status_data = {
            "internet_online": internet,
            "supabase": sup,
            "sqlite": sql,
            "is_syncing": is_syncing
        }
        self.system_handler.update_stats(status_data)

    def _load_table(self):
        """HUD_BRIDGE Shim: Notifica al handler que los registros han cambiado para refrescar el HUD JS."""
        logger.info("SYNC: Sincronización finalizada, refrescando datos en el HUD...")
        if hasattr(self, 'vault_handler'):
            # Esto dispara recordsChanged que el JS escucha para re-ejecutar tableManager.loadRecords()
            self.vault_handler.recordsChanged.emit()

    def on_sync_triggered(self):
        """Trigger global sync protocol using inherited DashboardSyncActions logic."""
        logger.info("SYNC: Manual protocol triggered via HUD.")
        try:
            self._on_sync()
        except Exception as e:
            logger.error(f"SYNC_ERROR: {e}")
            if hasattr(self, 'sync_completed'):
                self.sync_completed.emit(str(e))

    def _on_sync(self):
        """Override de DashboardSyncActions para evitar mensajes nativos al sincronizar offline."""
        if not getattr(self, 'internet_online', False):
            # En lugar de mostrar un diálogo nativo, enviar directo al HUD
            if hasattr(self, 'sync_completed'):
                self.sync_completed.emit("OFFLINE:_ERROR_SINCRO_INTERNET")
            return

        def sync_operation(progress_callback):
            stats = self.sync_manager.sync(
                progress_callback=progress_callback, 
                cloud_user_id=self.user_profile.get("id")
            )
            self.sm.log_event("SYNC_BIDIRECCIONAL", details="Sincronización manual ejecutada desde V2 HUD")
            return stats

        self._run_sync_op("SINCRO_NUBE", sync_operation, show_summary=True)

    def _on_force_password_change(self):
        """[SECURITY] Muestra el diálogo de cambio de clave forzoso."""
        logger.info("CORE: Lanzando Diálogo de Cambio de Clave Forzoso...")
        from src.presentation.change_password_dialog import ChangePasswordDialog
        
        # El diálogo bloquea la UI (Modal) para asegurar que el usuario cambie la clave
        dialog = ChangePasswordDialog(
            self.sm, self.um, 
            user_profile=self.user_profile,
            sync_manager=self.sync_manager,
            parent=self
        )
        dialog.exec_()

    def closeEvent(self, event):
        """Limpieza de hilos al cerrar."""
        self.conn_worker.stop()
        self.heur_worker.running = False
        super().closeEvent(event)

    def _run_sync_op(self, title, func, show_summary=False):
        """Override de DashboardSyncActions para usar el Modal Táctico del HUD con multihilo."""
        try:
            import threading
            self.syncing_active = True
            self.sync_started.emit(title)
            
            def cb(val, msg):
                # Emitir señal de progreso (Qt se encarga de la seguridad entre hilos)
                self.sync_progress.emit(val, msg)
            
            def target_wrapper():
                try:
                    stats = func(progress_callback=cb)
                    
                    # Al finalizar, recargar datos y emitir completado en el hilo principal
                    self._load_table()
                    
                    if show_summary and isinstance(stats, dict):
                        self.sync_completed.emit(stats)
                    else:
                        # Close via JS directly
                        self.page.runJavaScript("closeSyncModal()")
                except Exception as e:
                    logger.error(f"SYNC THREAD ERROR: {e}")
                    self.sync_completed.emit({"error": str(e)})
                finally:
                    self.syncing_active = False

            # Iniciar el hilo de sincronización
            thread = threading.Thread(target=target_wrapper, daemon=True)
            thread.start()
                
        except Exception as e:
            logger.error(f"SYNC OP INIT ERROR: {e}")
            self.syncing_active = False
            self.sync_completed.emit({"error": str(e)})

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialize Managers (same as src/main.py bootstrap)
    try:
        sm = SecretsManager()
        um = UserManager(sm)
        sync = SyncManager(sm, SUPABASE_URL, SUPABASE_KEY)
        logger.info("Standalone V2 Boot: managers initialized.")
    except Exception as e:
        logger.error(f"Boot failed: {e}")
        sys.exit(1)

    # Determine active user (first available local user or logged-in user)
    # For standalone testing, we auto-login as the first available user
    import os
    from src.infrastructure.config.path_manager import PathManager
    vault_dbs = list(PathManager.DATA_DIR.glob("vault_*.db"))

    if not vault_dbs:
        logger.error("No vault databases found. Run the main app first to create a user.")
        sys.exit(1)

    # Extract username from filename: "vault_USERNAME.db"
    username_guess = vault_dbs[0].stem.replace("vault_", "")
    logger.info(f"Standalone Boot: Detected user '{username_guess}'. Enter master password at login prompt.")

    # Launch V2 login page first (the HTML login handles auth)
    user_profile = {
        "username": username_guess,
        "role": "admin",
        "vault_name": "VAULT CORE"
    }

    window = MainWindow(secrets_manager=sm, sync_manager=sync, user_manager=um, user_profile=user_profile)
    window.show()
    sys.exit(app.exec_())
