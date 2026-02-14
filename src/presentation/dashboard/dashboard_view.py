import logging
import winsound
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import QTimer, QSettings, Qt, QDateTime, QDate, QEvent, pyqtSignal

from src.infrastructure.guardian_ai import GuardianAI
from src.presentation.login_view import LoginView
from src.presentation.dashboard.dashboard_ui import DashboardUI
from src.presentation.dashboard.dashboard_actions import DashboardActions
from src.presentation.dashboard.dashboard_table import DashboardTableManager
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.dialogs.ghost_fix_dialog import GhostFixDialog
from src.presentation.notifications.notification_manager import Notifications
from src.presentation.dashboard.dashboard_workers import ConnectivityWorker, HeuristicWorker
from src.presentation.dashboard.voice_search_worker import VoiceSearchWorker

INACTIVITY_LIMIT_MS = 10 * 60 * 1000

logger = logging.getLogger(__name__)

class DashboardView(QWidget, DashboardUI, DashboardActions, DashboardTableManager):
    # [SIGNAL FIX] Canal seguro para refrescar la UI desde hilos de fondo
    sync_finished = pyqtSignal()
    
    def __init__(self, sm, sync_manager, user_manager, user_profile, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.sync_manager = sync_manager
        self.user_manager = user_manager
        self.user_profile = user_profile
        self.current_username = user_profile.get("username", "Unknown")
        self.current_role = user_profile.get("role") or "user"
        self.user_role = self.current_role  # Alias para compatibilidad
        self.sm.user_role = self.current_role.lower() # Sincronizar con motor de seguridad

        # Prevenir múltiples ejecuciones de atajos
        self._shortcut_active = False

        from src.infrastructure.config.path_manager import PathManager
        self.settings = QSettings(ThemeManager.APP_ID, f"VultraxCore_{self.current_username}")
        self.global_settings = QSettings(str(PathManager.GLOBAL_SETTINGS_INI), QSettings.IniFormat)
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager # [COMPAT FIX] for table and ui mixins
        
        # [MULTI-USER LANGUAGE FIX] Prefer per-user settings, fallback to global
        user_lang = self.settings.value("language") or self.global_settings.value("language")
        if user_lang and user_lang in ["ES", "EN"]:
            MESSAGES.LANG = user_lang
            logger.info(f"Language Synced: {user_lang} for {self.current_username}")
        
        # [THEME-PER-USER FIX] Load and apply theme
        saved_theme = self.settings.value("theme_active") or self.global_settings.value("theme_active", "tactical_dark")
        self.theme_manager.theme_changed.connect(lambda: self.theme_manager.apply_app_theme(QApplication.instance()))
        self.theme_manager.theme_changed.connect(self._refresh_all_widget_themes)
        self.theme_manager.set_theme(saved_theme)
        self.theme_manager.apply_app_theme(QApplication.instance())
        self._refresh_all_widget_themes()
        
        # [RECURSION PROTECTION] Move window setup from showEvent to __init__
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._is_showing_maximized = False
        # We don't apply setStyleSheet yet because UI is not built, 
        # BUT we must ensure that when _build_ui is called, it uses the correct theme colors?
        # Actually, setStyleSheet works on the widget directly. 
        # However, _build_ui loads widgets which might need the theme active.
        
        self.style_cache = {}
        
        # Cargar configuración de IA personalizada del usuario (SaaS Sync)
        ai_provider = self.settings.value("ai_provider_active", "Google Gemini ✨")
        
        # Obtener la llave específica según el proveedor para el arranque
        ai_key = ""
        if "Gemini" in ai_provider: ai_key = self.settings.value("ai_key_gemini", "")
        elif "ChatGPT" in ai_provider: ai_key = self.settings.value("ai_key_chatgpt", "")
        elif "Claude" in ai_provider: ai_key = self.settings.value("ai_key_claude", "")
        
        self.ai = GuardianAI(engine=ai_provider, api_key=ai_key)
        self.ai.configure_engine(ai_provider, ai_key) # Forzar activación

        self._build_ui()
        self._init_state()
        self._init_watcher() # New unified initialization
        self._connect_ui_signals()
        
        # Conectar señal de Ghost Sync
        self.sync_finished.connect(self._load_table)
        
        # INICIALIZACIÓN TÁCTICA DE BARRA DE SESIÓN
        if hasattr(self, 'watcher') and hasattr(self, 'session_bar'):
            # [DIAGNOSTIC] Log exact initial timeout
            logger.info(f"Session Bar Init: 0 to {self.watcher.timeout_ms // 1000}s")
            self.session_bar.setRange(0, self.watcher.timeout_ms // 1000)
            self.session_bar.setValue(self.watcher.timeout_ms // 1000)
            
            # Conexión Robusta a cambios de timeout
            self.watcher.timeout_changed.connect(self._on_timeout_duration_changed)
    
        # --- Hilo de conectividad ---
        self.conn_worker = ConnectivityWorker(self.sync_manager, self.sm)
        self.conn_worker.status_updated.connect(self._on_connectivity_update)
        self.conn_worker.start()

        # --- Hilo de Heurística (Senior Security) ---
        self.heuristic_worker = HeuristicWorker(self.sm, self.user_manager)
        self.heuristic_worker.stats_updated.connect(self._on_heuristic_update)
        self.heuristic_worker.start()
        
        # [NEW] Activate Vultrax Widget Bar
        self._setup_vultrax_widget_bar()

        # --- Voice Search Engine ---
        self.voice_worker = VoiceSearchWorker(self)
        self.voice_worker.result_ready.connect(self._on_voice_search_result)
        self.voice_worker.error_occurred.connect(self._on_voice_search_error)
        self.voice_worker.listening_started.connect(self._on_voice_listening_started)
        self.voice_worker.listening_finished.connect(self._on_voice_listening_finished)

        self._apply_role_restrictions()
        self._load_ui_settings()
        self._load_generator_settings() 
        
        # [STARTUP OPTIMIZATION] Carga inmediata de datos locales
        self._load_table()
        
        # [STARTUP OPTIMIZATION] Sincronización silenciosa en segundo plano post-arranque
        # Esperamos 1.5 segundos para que la UI se estabilice antes de la ráfaga de red
        QTimer.singleShot(1500, self._full_sync_async)

        # [NET CODE] Enforce removal of global filters if they persisted
        try: QApplication.instance().removeEventFilter(self)
        except: pass

    def _on_timeout_duration_changed(self, ms):
        """Sincronización LIVE: Reacciona al cambio de ajustes instantáneamente."""
        new_sec = ms // 1000
        logger.info(f"Inactivity Timeout Changed: {new_sec}s")
        
        if hasattr(self, 'session_bar'):
            self.session_bar.setRange(0, new_sec)
            self.session_bar.setValue(new_sec)
        
        if hasattr(self, 'lbl_countdown'):
            mins = new_sec // 60
            secs = new_sec % 60
            self.lbl_countdown.setTime(f"{mins:02d}:{secs:02d}")
            self.lbl_countdown.setStatus("OK")

    def eventFilter(self, obj, event):
        """
        [PROVISIONAL FIX] Bloquea cualquier eventFilter heredado que pudiera 
        estar causando recursión infinita en clases mixin o padres.
        """
        return False

    def _setup_vultrax_widget_bar(self):
        """Layout is now statically managed in DashboardUI for better stability."""
        pass

    def _update_session_bar(self):
        """Actualiza la barra de progreso de sesión basada en el InactivityWatcher."""
        if hasattr(self, "watcher") and hasattr(self, "session_bar"):
            timer = self.watcher.timer
            remaining = timer.remainingTime() # ms
            
            if remaining >= 0:
                val_sec = remaining // 1000
                self.session_bar.setValue(val_sec)
                
                # Actualizar texto numérico (Fixing 00:00 issue)
                mins = val_sec // 60
                secs = val_sec % 60
                time_str = f"{mins:02d}:{secs:02d}"
                
                if hasattr(self, 'lbl_countdown'):
                    self.lbl_countdown.setTime(time_str)
                
                # [PERFORMANCE FIX] Only repaint if state changes
                new_state = "OK"
                style = ""
                
                colors = self.theme_manager.get_theme_colors()
                if val_sec < 30: 
                    new_state = "ERROR"
                    style = f"QProgressBar::chunk {{ background-color: {colors.get('danger', '#ef4444')}; }}"
                elif val_sec < 60: 
                    new_state = "WARNING"
                    style = f"QProgressBar::chunk {{ background-color: {colors.get('warning', '#f59e0b')}; }}"
                
                last_state = getattr(self, "_last_bar_state", None)
                if new_state != last_state:
                    self.session_bar.setStyleSheet(style)
                    self._last_bar_state = new_state
                    
                if hasattr(self, 'lbl_countdown'): 
                    self.lbl_countdown.setStatus(new_state)
            else:
                # Si es -1 (detenido/timeout), forzar a 0
                self.session_bar.setValue(0)
                if hasattr(self, 'lbl_countdown'): 
                    self.lbl_countdown.setTime("00:00")
                    self.lbl_countdown.setStatus("ERROR")

    def showEvent(self, event):
        """Asegura que el Dashboard se muestre maximizado de forma segura."""
        if not self._is_showing_maximized:
            self._is_showing_maximized = True
            self.showMaximized() 
        super().showEvent(event)
        
    def _load_table(self):
        """Sobrecarga el cargado de tabla para disparar el motor heurístico asíncrono."""
        super()._load_table()
        if hasattr(self, "heuristic_worker"):
            # Delay para permitir que la UI respire antes del escaneo
            QTimer.singleShot(800, self.heuristic_worker.trigger_analysis)

    def keyPressEvent(self, event):
        """Captura atajos de teclado globales para el dashboard."""
        # --- ATAJO DE BLOQUEO MANUAL (Ctrl + L) ---
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_L:
            logger.info("Manual locking requested via Ctrl+L")
            self.lock_app()
            return

        super().keyPressEvent(event)

    def _connect_ui_signals(self):
        """Conecta cada botón de la nueva interfaz modular con su lógica en DashboardActions."""
        # TopBar
        # TopBar (Global Control Center)
        # [UI CLEANUP] TopBar buttons removed.
            
        # Search HUD Integration
        if hasattr(self, 'dash_search'):
            self.dash_search.textChanged.connect(self._on_search_changed)
            
        if hasattr(self, 'search_vault'):
            self.search_vault.textChanged.connect(self._on_search_changed)
        
        # Action Buttons Integration
        if hasattr(self, 'btn_add_dash'):
            self.btn_add_dash.clicked.connect(self._on_add)
        
        # Legacy/Sidebar refs
        if hasattr(self, 'btn_add'): self.btn_add.clicked.connect(self._on_add)
        self.btn_sync.clicked.connect(self._on_sync)
        if hasattr(self, 'btn_delete'): self.btn_delete.clicked.connect(self._on_delete)
        
        # Dedicated Vault View Buttons
        if hasattr(self, 'btn_add_vault'): self.btn_add_vault.clicked.connect(self._on_add)
        if hasattr(self, 'btn_sync_vault'): self.btn_sync_vault.clicked.connect(self._on_sync)
        if hasattr(self, 'btn_import'): self.btn_import.clicked.connect(self._on_import)
        if hasattr(self, 'btn_export'): self.btn_export.clicked.connect(self._on_export)
        if hasattr(self, 'btn_template'): self.btn_template.clicked.connect(self._on_download_template)
        if hasattr(self, 'btn_voice_search'): self.btn_voice_search.clicked.connect(self._toggle_voice_search)
        
        # Action Bar (Float Bar Vault)
        if hasattr(self, 'btn_vault_view'): self.btn_vault_view.clicked.connect(self._on_view_selected)
        if hasattr(self, 'btn_vault_copy'): self.btn_vault_copy.clicked.connect(self._on_copy_selected)
        if hasattr(self, 'btn_vault_edit'): self.btn_vault_edit.clicked.connect(self._on_edit_selected)
        if hasattr(self, 'btn_vault_delete'): self.btn_vault_delete.clicked.connect(self._on_delete_selected)
        if hasattr(self, 'btn_vault_deselect'): self.btn_vault_deselect.clicked.connect(self._deselect_all_vault)
        
        # Dual Generators & Mantenimiento (Settings Page)
        if hasattr(self, 'btn_generate_drawer'): self.btn_generate_drawer.clicked.connect(self._generate_password_advanced)
        if hasattr(self, 'btn_generate_ai'): self.btn_generate_ai.clicked.connect(self._on_generate_ai)
        if hasattr(self, 'length_slider'): self.length_slider.valueChanged.connect(self._on_length_changed)
        if hasattr(self, 'cb_upper'): self.cb_upper.stateChanged.connect(self._save_generator_settings)
        if hasattr(self, 'cb_lower'): self.cb_lower.stateChanged.connect(self._save_generator_settings)
        if hasattr(self, 'cb_digits'): self.cb_digits.stateChanged.connect(self._save_generator_settings)
        if hasattr(self, 'cb_symbols'): self.cb_symbols.stateChanged.connect(self._save_generator_settings)
        if hasattr(self, 'length_slider'): self.length_slider.sliderReleased.connect(self._save_generator_settings)
        
        # NUEVO: Ajustes Reactivos (Tema, Idioma y Timer)
        if hasattr(self, 'combo_theme'): self.combo_theme.activated.connect(lambda: self._save_settings_from_ui(silent=True))
        if hasattr(self, 'combo_lang'): self.combo_lang.activated.connect(self._on_lang_changed)
        # Lock time connection is handled in dashboard_ui.py
        
        
        # Guardian AI Hub
        if hasattr(self, 'btn_ai_invoke'): self.btn_ai_invoke.clicked.connect(self._on_ai_audit)
        
        # Admin Panel (Danger Zone) - Now handled internally by AdminPanel component
        pass
        
        # Historial Sync
        if hasattr(self, 'btn_refresh_audit_cloud'): self.btn_refresh_audit_cloud.clicked.connect(self._on_sync_audit)

        # Password Health Action
        if hasattr(self, 'btn_fix_health'): self.btn_fix_health.clicked.connect(self._on_fix_password_health)

        # NUEVAS CONEXIONES BENTO (Navegación Táctica)
        if hasattr(self, 'btn_go_vault'):
            if self.current_role.lower() == "admin":
                self.btn_go_vault.clicked.connect(lambda: self.admin_panel._on_manage_users())
            else:
                def go_vault():
                    self.main_stack.setCurrentWidget(self.view_vault)
                    self.btn_nav_vault.setChecked(True)
                self.btn_go_vault.clicked.connect(go_vault)
                
        if hasattr(self, 'btn_go_activity'): 
            def go_activity():
                self.main_stack.setCurrentWidget(self.view_activity)
                self.btn_nav_activity.setChecked(True)
            self.btn_go_activity.clicked.connect(go_activity)
            
        if hasattr(self, 'btn_go_ai'): 
            def go_ai():
                self.main_stack.setCurrentWidget(self.view_ai)
                self.btn_nav_ai_side.setChecked(True)
            self.btn_go_ai.clicked.connect(go_ai)
            
        if hasattr(self, 'card_ai_guardian'):
            def go_ai_from_card():
                self.main_stack.setCurrentWidget(self.view_ai)
                self.btn_nav_ai_side.setChecked(True)
            self.card_ai_guardian.clicked.connect(go_ai_from_card)
        if hasattr(self, 'btn_go_monitor'): self.btn_go_monitor.clicked.connect(self._open_monitor_sessions)
        if hasattr(self, 'btn_go_sync'): self.btn_go_sync.clicked.connect(self._on_sync)
        if hasattr(self, 'btn_go_services'): self.btn_go_services.clicked.connect(self._on_add)
        if hasattr(self, 'btn_ai_analysis'): self.btn_ai_analysis.clicked.connect(self._on_ai_audit)
        
        # [SIGNAL-BASED INTERACTION] No more eventFilters
        
        # [SIGNAL-BASED INTERACTION] No more eventFilters
        if hasattr(self, 'gauge'): self.gauge.clicked.connect(self._on_ai_audit)
        if hasattr(self, 'ai_radar'): self.ai_radar.clicked.connect(self._on_ai_audit)
        
        # DASHBOARD QUICK SEARCH (Fast Access Protocol)
        if hasattr(self, 'dash_search'):
            self.dash_search.returnPressed.connect(self._on_dash_search_return)

        # Settings & Data Management
        if hasattr(self, 'btn_nav_settings'): self.btn_nav_settings.clicked.connect(self._on_settings)
        if hasattr(self, 'btn_save_settings'): self.btn_save_settings.clicked.connect(self._save_settings_from_ui)
        if hasattr(self, 'btn_change_pwd_real'): self.btn_change_pwd_real.clicked.connect(self._on_change_password)
        if hasattr(self, 'btn_repair_vault_dashboard'): self.btn_repair_vault_dashboard.clicked.connect(self._on_repair_vault_dashboard)
        
        # [SIGNAL-BASED INTERACTION] No more eventFilters
        # if hasattr(self, 'ai_radar'): self.ai_radar.installEventFilter(self)
        
        # --- CONEXIONES DE TABLA (Premium Context Logic) ---
        self.table.cellClicked.connect(self._on_table_cell_clicked)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        if hasattr(self, 'table_vault'):
            self.table_vault.cellClicked.connect(self._on_table_cell_clicked)
            self.table_vault.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        
        if hasattr(self, 'btn_backup'): self.btn_backup.clicked.connect(self._on_backup)
        if hasattr(self, 'btn_restore'): self.btn_restore.clicked.connect(self._on_restore)
        if hasattr(self, 'btn_local_backup'): self.btn_local_backup.clicked.connect(self._on_local_backup)
        if hasattr(self, 'btn_local_restore'): self.btn_local_restore.clicked.connect(self._on_local_restore)
        if hasattr(self, 'btn_purge_private'): self.btn_purge_private.clicked.connect(self._on_purge_private)

    def _on_connectivity_update(self, internet, supabase_msg, sqlite_msg, sync_err=None, audit_err=None, is_syncing=False):
        """Recibe actualizaciones del hilo secundario y aplica estados a los widgets visuales."""
        self.internet_online = internet

        # 1. Internet Status (Radar Widget)
        self.status_internet.setOnline(internet)
        
        # 2. Supabase Status (Cloud Pulse Widget)
        is_sup_ok = "ONLINE" in supabase_msg.upper()
        self.status_supabase.setOnline(is_sup_ok)
            
        # 3. SQLite Status (Local Pulse Widget)
        is_sql_ok = "ONLINE" in sqlite_msg.upper()
        self.status_sqlite.setOnline(is_sql_ok)

        # 4. Sync Status Badge
        self.status_sync_badge.setSyncing(is_syncing)
        if sync_err:
            msg = f"Sincronización: ❌ Error ({sync_err})" if str(sync_err) == "400" else f"Sincronización: ⚠️ Warning ({sync_err})"
            self.status_sync_badge.setStatus(msg, "ERROR" if str(sync_err) == "400" else "WARNING")
            self.status_sync_badge.setToolTip(msg)
        else:
            self.status_sync_badge.setStatus("🔄 Sync", "OK")
            self.status_sync_badge.setToolTip("Sincronización: Todo al día 🔄")

        # 5. Audit Status Badge
        self.status_audit_badge.setSyncing(is_syncing)
        if audit_err:
            msg = f"Auditoría: ❌ Error ({audit_err})"
            self.status_audit_badge.setStatus(msg, "ERROR")
            self.status_audit_badge.setToolTip(msg)
        else:
            self.status_audit_badge.setStatus("🛡️ Audit", "OK")
            self.status_audit_badge.setToolTip("Auditoría: Integridad verificada 🛡️")

    def _on_heuristic_update(self, stats):
        """Aplica los resultados del análisis heurístico a la UI sin lag."""
        if not stats: return
        
        try:
            # 1. Gauge Principal
            self.gauge.value = stats["score"]
            
            # 2. Unidades Tácticas de Detalle
            if hasattr(self, 'unit_health'):
                h_val = stats['hygiene']
                h_status = "success" if h_val > 80 else "warning" if h_val > 50 else "critical"
                self.unit_health.set_value(f"{h_val}%", percent=h_val, color_name=h_status)
                
            if hasattr(self, 'unit_integrity'):
                m_val = stats['mfa']
                m_status = "info" if m_val > 80 else "warning"
                self.unit_integrity.set_value(f"{m_val}%", percent=m_val, color_name=m_status)
                
            if hasattr(self, 'unit_risk'):
                r_val = stats['risk'].upper()
                r_status = "success" if r_val == "LOW" else "warning" if r_val == "MEDIUM" else "critical"
                self.unit_risk.set_value(f"{r_val} {'🛡️' if r_val == 'LOW' else '⚠️'}", color_name=r_status)
                
            if hasattr(self, 'unit_protocol'):
                a_status = "success" if stats['audit'].upper() == "OK" else "critical"
                self.unit_protocol.set_value(f"{stats['audit'].upper()} {'✅' if a_status == 'success' else '⚠️'}", color_name=a_status)

            # 2a. New System Metrics (Filling Grid)
            if hasattr(self, 'unit_encryption'):
                self.unit_encryption.set_value("AES-256 GCM 🛡️", color_name="success")
                
            if hasattr(self, 'unit_storage'):
                import os
                try:
                    size_mb = os.path.getsize(self.sm.db_path) / (1024 * 1024)
                    self.unit_storage.set_value(f"{size_mb:.2f} MB 📊", color_name="info")
                except: pass
            
            # 2b. HEALTH REACTOR (Radial Gauge) UPDATE
            if hasattr(self, 'health_reactor'):
                self.health_reactor.set_data(score=stats.get("hygiene", 0))

            # Smart Text Logic (CrowdStrike Style)
            if hasattr(self, 'lbl_ph_smart_text'):
                weak_c = stats.get("weak_count", 0)
                reused_c = stats.get("reused_count", 0)
                hygiene = stats.get("hygiene", 100)
                
                msg = ""
                colors = self.theme_manager.get_theme_colors()
                if weak_c > 0:
                    msg = f"⚠️ High risk: {weak_c} weak passwords found"
                    color_tag = "danger"
                elif reused_c > 0:
                    msg = f"⚠️ Warning: {reused_c} reused passwords"
                    color_tag = "warning"
                elif hygiene == 100:
                    msg = "✅ System healthy — All checks passed"
                    color_tag = "success"
                else:
                    msg = "System analysis complete"
                    color_tag = "text_dim"
                
                color = colors.get(color_tag, "#94a3b8")
                
                self.lbl_ph_smart_text.setText(msg)
                self.lbl_ph_smart_text.setProperty("status", "critical" if weak_c > 0 else "warning" if reused_c > 0 else "success")
                self.lbl_ph_smart_text.style().unpolish(self.lbl_ph_smart_text)
                self.lbl_ph_smart_text.style().polish(self.lbl_ph_smart_text)
            
            # [RESTORED] Detailed Metrics Update
            if hasattr(self, 'lbl_ph_weak'): self.lbl_ph_weak.setText(str(stats.get('weak_count', 0)))
            if hasattr(self, 'lbl_ph_reused'): self.lbl_ph_reused.setText(str(stats.get('reused_count', 0)))
            if hasattr(self, 'lbl_ph_strong'): self.lbl_ph_strong.setText(str(stats.get('strong_count', 0)))
            if hasattr(self, 'lbl_ph_old'): self.lbl_ph_old.setText(str(stats.get('old_count', 0)))

            # 3. Tactical Radar Update
            # Guardar issues para el Ghost Fix Dialog
            self.last_heuristic_issues = stats.get("problematic_records", {})

            if hasattr(self, 'radar'):
                internet_stat = 100 if getattr(self, 'internet_online', False) else 20
                # [STRENGTH, AUTH, SYNC, HEALTH, ROTATION]
                radar_vals = [
                    stats.get("hygiene", 80),
                    stats.get("mfa", 70),
                    internet_stat,
                    max(20, 100 - (stats.get("weak_count", 0) * 10)),
                    max(20, 100 - (stats.get("old_count", 0) * 10))
                ]
                self.radar.setValues(radar_vals)

            # 3b. AI GUARDIAN REDESIGN RADAR (8-Axis Octagon)
            if hasattr(self, 'ai_radar'):
                internet_stat = 100 if getattr(self, 'internet_online', False) else 20
                # [STRENGTH, AUTH, HEALTH, ROTATION, INTEL, SYNC, RECORDS, RISK]
                ai_radar_vals = [
                    stats.get("hygiene", 80),
                    stats.get("mfa", 70),
                    max(20, 100 - (stats.get("weak_count", 0) * 10)),
                    max(20, 100 - (stats.get("old_count", 0) * 10)),
                    95, # Intel Score
                    internet_stat,
                    min(100, (stats.get("total_accounts", 0) / 50.0) * 100), # Records density
                    max(20, 100 - (stats.get("risk_factor", 0) * 10)) # Real Risk axis
                ]
                self.ai_radar.setValues(ai_radar_vals)
                
                # --- NEW: SYSTEM HEALTH & THREATS WIRING ---
                if hasattr(self, 'unit_score'):
                    self.unit_score.set_value(f"{stats['score']}%", percent=stats['score'], color_name="success" if stats['score'] > 80 else "warning")
                if hasattr(self, 'unit_status'):
                    status_txt = "OPTIMAL" if stats['score'] > 85 else "DEGRADED"
                    self.unit_status.set_value(status_txt, color_name="success" if status_txt == "OPTIMAL" else "warning")
                if hasattr(self, 'unit_load'):
                    import os
                    try:
                        size_mb = os.path.getsize(self.sm.db_path) / (1024 * 1024)
                        self.unit_load.set_value(f"{size_mb:.2f} MB", percent=min(100, int(size_mb * 5)), color_name="info")
                    except: pass
                
                if hasattr(self, 'unit_active_risks'):
                    total_risk = stats.get("weak_count", 0) + stats.get("reused_count", 0)
                    self.unit_active_risks.set_value(f"{total_risk} DETECTED", color_name="critical" if total_risk > 0 else "success")
                if hasattr(self, 'unit_intel_status'):
                    intel_txt = "MONITORING" if internet_stat > 50 else "OFFLINE"
                    self.unit_intel_status.set_value(intel_txt, color_name="success" if intel_txt == "MONITORING" else "danger")
                # -------------------------------------------
                
                # Header Status Logic (Synchronized with Password Health)
                if hasattr(self, 'lbl_dot_count'):
                    weak_c = stats.get("weak_count", 0)
                    reused_c = stats.get("reused_count", 0)
                    total_risk = weak_c + reused_c
                    self.lbl_dot_count.setText(f"🛡️ {total_risk} RISKS")
                    self.lbl_dot_count.setToolTip(f"⚠️ VULNERABILITIES DETECTED:\n• {weak_c} Weak Passwords (Score < 70)\n• {reused_c} Reused Passwords")
                if hasattr(self, 'lbl_ai_log_header'):
                    self.lbl_ai_log_header.setText(f"THREAT INTELLIGENCE FEED ({total_risk} DETECTIONS)")
                
                # [NEW] Populate the visual feed with intelligent insights
                self._update_ai_guardian_feed(stats)
            
            if hasattr(self, 'unit_auth_mfa'): 
                mfa_count = stats['mfa_users']
                total_users = stats['total_users']
                ratio = mfa_count / total_users if total_users > 0 else 1
                self.unit_auth_mfa.set_value(f"{mfa_count} / {total_users}", percent=int(ratio * 100), color_name="success" if ratio > 0.8 else "warning")

            if hasattr(self, 'unit_auth_admin'):
                count = stats['admin_no_mfa']
                self.unit_auth_admin.set_value(f"{'SECURE' if count == 0 else 'UNSECURED'} {'🛡️' if count == 0 else '⚠️'}", color_name="success" if count == 0 else "critical")
                if hasattr(self, 'badge_admin_alert'):
                    self.badge_admin_alert.setVisible(count > 0)
                    self.badge_admin_alert.setProperty("status", "critical")
                    if count > 0: self._start_admin_alert_pulse()
                
                # --- GLOBAL ENTERPRISE WARNING ---
                if hasattr(self, 'global_security_banner'):
                    self.global_security_banner.setVisible(count > 0)

            if hasattr(self, 'unit_auth_fails'):
                f_count = stats['failed_logins_24h']
                self.unit_auth_fails.set_value(f"{f_count} ATTEMPTS", percent=min(100, f_count * 20), color_name="critical" if f_count > 5 else "info")

            if hasattr(self, 'unit_auth_last'):
                l_val = str(stats.get('last_suspicious') or "--").upper()
                self.unit_auth_last.set_value(f"{l_val} {'✅' if l_val == '--' else '⚠️'}", color_name="info" if l_val == "--" else "warning")

            # 2e. New Auth Metrics (Filling Grid)
            if hasattr(self, 'unit_auth_sessions'):
                try:
                    import time
                    sessions = self.sync_manager.get_active_sessions() or []
                    active_count = sum(1 for s in sessions if (time.time() - (s.get("last_seen", 0))) < 300 and not s.get("is_revoked"))
                    self.unit_auth_sessions.set_value(f"{max(1, active_count)} ACTIVE ⚡", color_name="success")
                except: pass

            if hasattr(self, 'unit_auth_policy'):
                self.unit_auth_policy.set_value("BUSINESS STD 🏢", color_name="info")
            
            # 2d. Security Watch mini labels (Managed by QSS via ObjectName)
            # Already have tactical_metric_label objectNames from dashboard_ui.py
            pass

            # 3. Sincronizar con Barra de Protección y Colores
            if hasattr(self, 'bar_strength_fill') and hasattr(self, 'lbl_protection_status'):
                health = stats["score"]
                width_factor = health / 100.0
                bw = getattr(self.bar_strength, 'width', lambda: 180)()
                if not isinstance(bw, int): bw = 180
                
                self.bar_strength_fill.setFixedWidth(int(bw * width_factor))
                
                if health < 50: status_key = "critical"; status_txt = "PROTECTION: CRITICAL"
                elif health < 85: status_key = "warning"; status_txt = "PROTECTION: VULNERABLE"
                else: status_key = "success"; status_txt = "PROTECTION: REINFORCED"
                
                self.bar_strength_fill.setProperty("state", status_key)
                self.lbl_protection_status.setProperty("state", status_key)
                self.lbl_protection_status.setText(status_txt)
                
                # Refresh styles
                for w in [self.bar_strength_fill, self.lbl_protection_status]:
                    w.style().unpolish(w); w.style().polish(w)

        except (RuntimeError, AttributeError):
            # Ignorar errores si los widgets están siendo destruidos o aún no existen
            pass

    def _update_ai_guardian_feed(self, stats):
        """Populates the AI Guardian card's feed with tactical insights."""
        if not hasattr(self, 'ai_layout') or not self.ai_layout:
            return
            
        # 1. Clear existing items (except the header)
        while self.ai_layout.count() > 1:
            item = self.ai_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        # 2. Add Tactical Insights
        insights = []
        
        # Risk Factor Insight
        risk = stats.get("risk", "Low")
        if risk == "High":
             insights.append(("🔴 CRITICAL: Potential system compromise detected", "critical"))
        elif risk == "Medium":
             insights.append(("🟡 WARNING: Security posture degraded", "warning"))
        else:
             insights.append(("🟢 OK: Neural shield at 100% efficiency", "success"))
             
        # Specific Vulnerabilities
        weak = stats.get("weak_count", 0)
        reused = stats.get("reused_count", 0)
        old = stats.get("old_count", 0)
        
        if weak > 0: insights.append((f"⚠️ {weak} weak entropy keys identified", "warning"))
        if reused > 0: insights.append((f"⚠️ {reused} keys found in multiple clusters", "warning"))
        if old > 0: insights.append((f"📅 {old} records requiring rotation", "info"))
        
        # Admin / MFA
        admin_mfa = stats.get("admin_no_mfa", 0)
        if admin_mfa > 0:
            insights.append((f"❌ {admin_mfa} privileged accounts without MFA", "critical"))
            
        # Fails
        fails = stats.get("failed_logins_24h", 0)
        if fails > 10:
            insights.append((f"📡 Abnormal login activity: {fails} fails/24h", "critical"))
        elif fails > 0:
            insights.append((f"ℹ️ Login noise detected: {fails} fails in 24h", "info"))
            
        colors = self.theme_manager.get_theme_colors()
        color_map = {
            "critical": colors.get("danger", "#ef4444"),
            "warning": colors.get("warning", "#f59e0b"),
            "success": colors.get("success", "#22c55e"),
            "info": colors.get("info", "#06b6d4")
        }
        
        # 3. Render items
        for text, status in insights:
            from PyQt5.QtWidgets import QLabel
            lbl = QLabel(f"> {text}")
            lbl.setStyleSheet(f"color: {color_map.get(status, '#94a3b8')}; font-size: 10px; font-family: 'Consolas'; font-weight: 500;")
            lbl.setWordWrap(True)
            self.ai_layout.addWidget(lbl)
            
        # Add filler if empty
        if len(insights) == 0:
            lbl = QLabel("> No immediate threats detected.")
            lbl.setStyleSheet(f"color: {colors.get('text_dim', '#94a3b8')}; font-style: italic; font-size: 10px;")
            self.ai_layout.addWidget(lbl)
            
        self.ai_layout.addStretch()

    def _on_fix_password_health(self):
        """Abre el diálogo Ghost Fix para resolver vulnerabilidades de forma táctica."""
        issues = getattr(self, 'last_heuristic_issues', {})
        if not issues or (not issues.get('reused') and not issues.get('weak')):
            # Si no hay nada que arreglar según el último escaneo, ir a la bóveda
            if hasattr(self, 'main_stack') and hasattr(self, 'view_vault'):
                self.main_stack.setCurrentWidget(self.view_vault)
            return

        dialog = GhostFixDialog(issues, self.sm, self)
        dialog.exec_()

    def _start_admin_alert_pulse(self):
        """Inicia una animación de pulsación para el badge de pánico."""
        if not hasattr(self, '_admin_pulse_timer'):
            from PyQt5.QtCore import QTimer
            self._admin_pulse_timer = QTimer(self)
            self._admin_pulse_state = True
            def toggle():
                colors = self.theme_manager.get_theme_colors()
                is_ghost = getattr(self, 'ghost_enabled', False)
                danger_c = colors.get("danger", "#ef4444")
                c = danger_c 
                bc = c if self._admin_pulse_state else "transparent"
                
                if hasattr(self, 'badge_admin_alert'):
                    self.badge_admin_alert.setStyleSheet(
                        f"color: {c}; font-weight: 900; font-size: 10px; padding: 4px; "
                        f"border: 2px solid {bc}; "
                        "border-radius: 4px;"
                    )
                
                # Sync global banner pulse if visible
                if hasattr(self, 'global_security_banner') and self.global_security_banner.isVisible():
                    b_c = c if self._admin_pulse_state else "transparent"
                    
                    # Convert hex to rgba for glass effect if needed, but for now just use simple bg
                    self.global_security_banner.setStyleSheet(
                        f"background-color: {colors.get('bg_sec_95', 'rgba(15,23,42,0.9)')}; "
                        f"border: 1px solid {b_c}; "
                        "border-radius: 12px;"
                    )
                self._admin_pulse_state = not self._admin_pulse_state
            self._admin_pulse_timer.timeout.connect(toggle)
            self._admin_pulse_timer.start(500)

    def center_on_screen(self):
        """Centra la ventana principal en el monitor actual."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry(QDesktopWidget().cursor().pos())
        size = self.geometry()
        x = (screen.width() - size.width()) // 2 + screen.left()
        y = (screen.height() - size.height()) // 2 + screen.top()
        self.move(x, y)

    def _init_state(self):
        self.internet_online = False
        self.syncing_active = False
        self.supabase_anim_active = False
        self.internet_frames = ["🌐🟢 Conectado", "📡🟢 Transmitiendo...", "🔄🟢 Activo"]
        self.internet_frame_index = 0
        self.sync_frames = ["⬆️⬇️ Sync...", "⬆️⬇️ Sync..", "⬆️⬇️ Sync."]
        self.sync_frame_index = 0
        self.supabase_frames = ["Supabase: 🟢 Online", "Supabase: 🟢 Online", "Supabase: 🟢 Online"]
        self.supabase_frame_index = 0
        
        # --- NUEVO: SINCRONIZACIÓN DE IDENTIDAD ---
        # Priorizar el nombre que viene del perfil validado
        v_name = self.user_profile.get("vault_name")
        if not v_name and self.sm:
            v_name = self.sm.get_meta("instance_name")
            
        if v_name:
            if hasattr(self, 'identity_banner'): self.identity_banner.set_vault_name(v_name)
            if hasattr(self, 'lbl_v_name'): self.lbl_v_name.setText(v_name.upper())
            if hasattr(self, 'identity_banner_vault'): self.identity_banner_vault.set_vault_name(v_name)
            # Persistencia local del nombre para sesiones offline
            if self.sm: self.sm.set_meta("instance_name", v_name)
            logger.info(f"Visual identity established: {v_name}")

    def _start_clock(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        dt = QDateTime.currentDateTime()
        self.status_datetime.setText(dt.toString("dd/MM/yyyy HH:mm:ss"))

    def _init_watcher(self):
        """Configuración unificada del vigilante de inactividad (NUCLEAR REFRESH)."""
        if not hasattr(self, '_clock_started'):
            self._start_clock()
            self._clock_started = True
        
        from src.presentation.inactivity_watcher import GlobalInactivityWatcher
        
        # [SENIOR DIAGNOSTIC] Cargar configuración específica con traza de origen
        self.settings.sync() 
        val = self.settings.value("auto_lock_time", 10)
        timeout_min = int(val)
        self.auto_lock_ms = timeout_min * 60 * 1000
        
        logger.info(f"Nuclear Sync: User={self.current_username}, Timeout={timeout_min} Min")
        
        # Actualizar el singleton de forma imperativa
        self.watcher = GlobalInactivityWatcher.get_instance(self.auto_lock_ms, self.lock_app)
        self.watcher.start()
        
        # Asegurar que la UI visual refleje el cambio inmediatamente
        self._on_timeout_duration_changed(self.auto_lock_ms)

        # [PREMIUM FIX] Prevenir fuga de timers al re-inicializar
        for timer_attr in ['session_timer', 'heartbeat_timer', 'auto_sync_timer']:
            if hasattr(self, timer_attr):
                old_timer = getattr(self, timer_attr)
                if old_timer: old_timer.stop(); old_timer.deleteLater()

        # Timer para feedback visual de sesión (barra de progreso)
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self._update_session_bar)
        self.session_timer.start(1000)

        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self._send_heartbeat)
        self.heartbeat_timer.start(30000)
        
        # Auto-sync periódico cada 2 minutos
        self.auto_sync_timer = QTimer(self)
        self.auto_sync_timer.timeout.connect(self._auto_sync_on_login)
        self.auto_sync_timer.start(120000) 

    def logout(self):
        self.sm.log_event("LOGOUT", details="Sesión cerrada manualmente")
        if hasattr(self, "watcher"): self.watcher.stop()
        self.hide()
        # FIX SENIOR: Pasar UserManager explícitamente para evitar crash
        self.login_window = LoginView(user_manager=self.user_manager, on_success=self._on_relogin_success)
        self.login_window.show()

    def _on_relogin_success(self, password, totp, data):
        """Restaura el acceso a la bóveda tras un auto-bloqueo exitoso."""
        try:
            self.sm.set_active_user(self.current_username, password)
            self.show()
            # Reiniciar timer de inactividad
            if hasattr(self, "watcher"): self.watcher.start()
        except Exception as e:
            PremiumMessage.error(self, MESSAGES.VAULT.TITLE_CRITICAL, f"Error al restaurar sesión: {e}")

    # [ARCHITECTURAL SHIFT] No more eventFilter logic in this class.
    # Inactivity monitoring is now handled by the GlobalInactivityWatcher (Singleton).

    def lock_app(self):
        """
        PROTOCOLO THE GHOST LOCK: Cierre de emergencia por inactividad.
        """
        logger.warning(f"Tactical Lock Triggered | Visible: {self.isVisible()}")
        
        if not self.isVisible(): 
            logger.debug("Ignoring lock call because window is not visible.")
            return
        
        if hasattr(self, "watcher"): self.watcher.stop()
        
        # 1. PURGA DE SEGURIDAD
        if self.sm:
            try:
                self.sm.cleanup_vault_cache()
                logger.info("Cache and keys purged successfully during lock.")
            except Exception as e:
                logger.error(f"Failed to purge cache during lock: {e}")

        # 2. Cierre de sub-ventanas
        for widget in QApplication.topLevelWidgets():
            if widget != self and widget.isVisible():
                widget.close()
        
        self.hide()
        
        # 3. LANZAR PANTALLA DE BLOQUEO (Esfera de Neón)
        try:
            from src.presentation.widgets.lock_sphere import HyperRealVaultCore
            v_name = "VULTRAX CORE"
            if self.sm: v_name = self.sm.get_meta("instance_name") or "VULTRAX CORE"
            
            self.lock_screen = HyperRealVaultCore(vault_name=v_name)
            # Al desbloquear (Presionar ENTER en la esfera), volvemos al login real
            self.lock_screen.unlocked.connect(self._show_login_after_lock)
            self.lock_screen.show()
            logger.info("Security sphere (Neon Ghost) deployed.")
        except Exception as e:
            logger.error(f"Failed to load lock screen sphere: {e}")
            self._show_login_after_lock()

    def _show_login_after_lock(self):
        """Muestra el diálogo de login tras el desbloqueo de la esfera."""
        logger.info("Restoring access after sphere unlock.")
        # Reiniciar el contador visual para cuando el usuario vuelva a entrar
        if hasattr(self, "watcher"): self.watcher.start()
        
        self.login_view = LoginView(
            user_manager=self.user_manager, 
            prefill_user=self.current_username, 
            on_success=self._on_relogin_success
        )
        self.login_view.show()

    def _apply_role_restrictions(self):
        """Aplica protocolos de seguridad corporativa: Restringe accesos críticos según el ROL."""
        is_admin = (self.current_role.upper() == "ADMIN")
        
        # 1. Sidebar: Ocultar Panel Admin y AI para usuarios normales
        if hasattr(self, 'btn_nav_users'): self.btn_nav_users.setVisible(is_admin)
        
        # 2. Acciones Críticas en Dashboard
        if hasattr(self, 'btn_delete'): self.btn_delete.setVisible(is_admin) # Botón global de borrar (solo admin)
        
        # 3. Acciones de Mantenimiento Local (Habilitadas para todos para respaldo personal)
        if hasattr(self, 'btn_import'): self.btn_import.setVisible(True)         # RESTAURADO
        if hasattr(self, 'btn_local_backup'): self.btn_local_backup.setVisible(True)   # Seguridad local personal
        if hasattr(self, 'btn_local_restore'): self.btn_local_restore.setVisible(True)  # Recuperación local personal
        
        # 4. Acciones de Administración Crítica (Solo Admin)
        if hasattr(self, 'btn_export'): self.btn_export.setVisible(is_admin)     # Evitar fuga masiva de datos por usuarios
        if hasattr(self, 'btn_backup'): self.btn_backup.setVisible(is_admin)     # UPLOAD NUBE Manual
        if hasattr(self, 'btn_restore'): self.btn_restore.setVisible(is_admin)    # DOWNLOAD NUBE Manual
        if hasattr(self, 'btn_repair_vault_dashboard'): self.btn_repair_vault_dashboard.setVisible(is_admin) # Crítico: Solo el Admin repara llaves
        
        # 5. Global Activity Filters (Only Admin)
        if hasattr(self, 'btn_filter_global'): self.btn_filter_global.setVisible(is_admin)
        if hasattr(self, 'btn_mod_global'): self.btn_mod_global.setVisible(is_admin)
        
        # 4. Mensaje Informativo
        if not is_admin:
            logger.info(f"Restricted Mode Active: User '{self.current_username}' operating under limited protocol.")
            # Cambiamos el color de la barra superior para indicar modo usuario (Style via QSS property)
            self.topbar.setProperty("user_mode", True)
            self.topbar.style().unpolish(self.topbar); self.topbar.style().polish(self.topbar)


    def _update_internet_realtime(self):
        """Usa el nuevo Socket Check ultra rápido de SyncManager."""
        self.internet_online = self.sync_manager.check_internet()
        self.status_internet.setOnline(self.internet_online)

    def _update_supabase_realtime(self):
        if not self.internet_online:
            self.status_supabase.setOnline(False)
            return
        is_sup_ok = self.sync_manager.check_supabase()
        self.status_supabase.setOnline(is_sup_ok)

    def _update_sqlite_realtime(self):
        try:
            self.sm.conn.execute("SELECT 1")
            self.status_sqlite.setOnline(True)
        except Exception:
            self.status_sqlite.setOnline(False)

    def _load_ui_settings(self):
        """Carga los valores guardados en los widgets de la página de ajustes (ROBUST PROTOCOL)."""
        self.settings.sync()
        
        # Motor y Keys
        provider = self.settings.value("ai_provider_active", "Desactivado")
        if hasattr(self, 'combo_provider'):
            idx = self.combo_provider.findText(provider)
            if idx >= 0: self.combo_provider.setCurrentIndex(idx)
        
        if hasattr(self, 'input_key_gemini'): self.input_key_gemini.setText(self.settings.value("ai_key_gemini", ""))
        if hasattr(self, 'input_key_chatgpt'): self.input_key_chatgpt.setText(self.settings.value("ai_key_chatgpt", ""))
        if hasattr(self, 'input_key_claude'): self.input_key_claude.setText(self.settings.value("ai_key_claude", ""))
        
        # Idioma
        if hasattr(self, 'combo_lang'):
            lang = self.settings.value("language", "ES")
            self.combo_lang.setCurrentIndex(0 if lang == "ES" else 1)

        # Tiempo de Bloqueo (Consistente con todo el sistema)
        if hasattr(self, 'combo_lock_time'):
            lock_time = self.settings.value("auto_lock_time", 10, type=int)
            mapping = {1: 0, 5: 1, 10: 2, 30: 3, 60: 4}
            self.combo_lock_time.setCurrentIndex(mapping.get(lock_time, 2))

        # Tema Visual (Mantenimiento de paridad con ThemeManager v2)
        if hasattr(self, 'combo_theme'):
            current_theme = self.settings.value("theme_active", "tactical_dark")
            mapping = {
                "tactical_dark": 0, 
                "phantom_glass": 1, 
                "bunker_ops": 2, 
                "obsidian_flow": 3,
                "neon_overdrive": 4,
                "saas_commercial": 5
            }
            self.combo_theme.setCurrentIndex(mapping.get(current_theme, 0))

    def _save_generator_settings(self, *args):
        """Persistencia de configuración del generador de contraseñas."""
        if hasattr(self, 'cb_upper'): self.settings.setValue("upper", self.cb_upper.isChecked())
        if hasattr(self, 'cb_lower'): self.settings.setValue("lower", self.cb_lower.isChecked())
        if hasattr(self, 'cb_digits'): self.settings.setValue("digits", self.cb_digits.isChecked())
        if hasattr(self, 'cb_symbols'): self.settings.setValue("symbols", self.cb_symbols.isChecked())
        if hasattr(self, 'length_slider'): self.settings.setValue("length", self.length_slider.value())

    def _load_generator_settings(self):
        """Carga la configuración del generador en la interfaz."""
        if hasattr(self, 'cb_upper'): self.cb_upper.setChecked(self.settings.value("upper", True, type=bool))
        if hasattr(self, 'cb_lower'): self.cb_lower.setChecked(self.settings.value("lower", True, type=bool))
        if hasattr(self, 'cb_digits'): self.cb_digits.setChecked(self.settings.value("digits", True, type=bool))
        if hasattr(self, 'cb_symbols'): self.cb_symbols.setChecked(self.settings.value("symbols", True, type=bool))
        if hasattr(self, 'length_slider'):
            val = self.settings.value("length", 20, type=int)
            self.length_slider.setValue(val)
            if hasattr(self, 'length_label'):
                self.length_label.setText(str(val))

    def _save_settings_from_ui(self, silent=False):
        """Protocolo de Guardado Blindado (NÚCLEO): Unifica todas las ramas de guardado."""
        logger.info(f"Iniciando guardado de ajustes (Silent={silent})...")
        try:
            # 1. Recopilar datos de la UI
            provider = self.combo_provider.currentText() if hasattr(self, 'combo_provider') else "Desactivado"
            key_gemini = self.input_key_gemini.text().strip() if hasattr(self, 'input_key_gemini') else ""
            key_chatgpt = self.input_key_chatgpt.text().strip() if hasattr(self, 'input_key_chatgpt') else ""
            key_claude = self.input_key_claude.text().strip() if hasattr(self, 'input_key_claude') else ""
            
            selected_lang = "ES"
            if hasattr(self, 'combo_lang'):
                selected_lang = "ES" if "Español" in self.combo_lang.currentText() else "EN"
            
            # 2. Persistencia DUAL (Per-User y Global para persistencia en Main)
            self.settings.setValue("ai_provider_active", provider)
            self.settings.setValue("ai_key_gemini", key_gemini)
            self.settings.setValue("ai_key_chatgpt", key_chatgpt)
            self.settings.setValue("ai_key_claude", key_claude)
            
            self.settings.setValue("language", selected_lang)
            if hasattr(self, 'global_settings'):
                self.global_settings.setValue("language", selected_lang)
            
            # Guardar Tiempo de Bloqueo
            lock_val = 10 
            if hasattr(self, 'combo_lock_time'):
                lock_text = self.combo_lock_time.currentText()
                nums = [int(s) for s in lock_text.split() if s.isdigit()]
                lock_val = nums[0] if nums else 10
            
            self.settings.setValue("auto_lock_time", lock_val)
            
            # Gestión de Tema (SINCRONIZACIÓN NUCLEAR)
            old_theme = self.settings.value("theme_active", "tactical_dark")
            if hasattr(self, 'combo_theme'):
                 mapping = {
                     0: "tactical_dark", 
                     1: "phantom_glass", 
                     2: "bunker_ops", 
                     3: "obsidian_flow",
                     4: "neon_overdrive",
                     5: "saas_commercial"
                 }
                 new_theme = mapping.get(self.combo_theme.currentIndex(), "tactical_dark")
                 self.settings.setValue("theme_active", new_theme)
                 if hasattr(self, 'global_settings'):
                     self.global_settings.setValue("theme_active", new_theme)
                 
                 if new_theme != old_theme: # Protocolo de Cambio de Fase
                     logger.info(f"Cambiando tema a {new_theme}...")
                     self.theme_manager.set_theme(new_theme)
                     from PyQt5.QtWidgets import QApplication
                     self.theme_manager.apply_app_theme(QApplication.instance())
                     self._refresh_all_widget_themes()
                     Notifications.show_toast(self, "Sistema Actualizado", f"Interfaz: {self.combo_theme.currentText()}", "🎨", "#06b6d4")

            # 3. Sincronización Física
            self.settings.sync()
            if hasattr(self, 'global_settings'): self.global_settings.sync()
            
            self._init_watcher()
            
            active_key = ""
            if "Gemini" in provider: active_key = key_gemini
            elif "ChatGPT" in provider: active_key = key_chatgpt
            elif "Claude" in provider: active_key = key_claude
            self.ai.configure_engine(provider, active_key)

            # 4. Gestión de Idioma (SaaS Logic)
            old_lang = MESSAGES.LANG
            MESSAGES.LANG = selected_lang
            self.sm.set_meta("language", selected_lang)
            
            if selected_lang != old_lang:
                logger.info(f"Idioma cambiado a {selected_lang}. Refrescando UI...")
                # NUCLEAR SYNC: Actualizar motor de mensajes y propagar a toda la UI
                MESSAGES.LANG = selected_lang
                if hasattr(self, 'retranslateUi'): self.retranslateUi()
                # ALTA VISIBILIDAD: Dialogo oficial para confirmar sincronía instantánea
                from src.presentation.ui_utils import PremiumMessage
                PremiumMessage.info(self, MESSAGES.COMMON.TITLE_INFO, MESSAGES.COMMON.MSG_LANG_SYNC)
            
            if not silent:
                PremiumMessage.success(self, MESSAGES.COMMON.TITLE_SUCCESS, MESSAGES.SETTINGS.MSG_SAVED)
                
        except Exception as e:
            logger.error(f"ERROR CRÍTICO al guardar ajustes: {e}")
            if not silent:
                PremiumMessage.critical(self, "Error de Sistema", f"No se pudieron salvar los ajustes: {str(e)}")

    def _on_settings(self):
        """En el modo SaaS, simplemente cambiamos a la vista de ajustes."""
        self.main_stack.setCurrentIndex(5)
        self.btn_nav_settings.setChecked(True)

    def _send_heartbeat(self):
        if self.internet_online:
            try: 
                self.sync_manager.send_heartbeat()
                
                # REVISIÓN DE SEGURIDAD (KILL SWITCH LISTENER)
                if self.sync_manager.check_revocation_status():
                    logger.critical(">>> [⚠️ SEGURIDAD] ¡Esta sesión ha sido revocada remotamente!")
                    self.hide()
                    
                    # PROTOCOLO DE LIMPIEZA DE RAM (SCRAMBLE)
                    if self.sm:
                        try:
                            self.sm.cleanup_vault_cache()
                        except Exception as e:
                            logger.error(f"Error during RAM cleanup after revocation: {e}")
                    

                    
            except Exception as e:
                logger.error(f"Error sending heartbeat or checking revocation status: {e}")

    def _connect_generator_signals(self):
        pass

    def _refresh_all_widget_themes(self):
        """Dispara el ciclo de refresco en todos los widgets con lógica de estilo personalizada."""
        # 1. Refresco Nuclear: Buscar recursivamente cualquier widget con refresh_theme
        from PyQt5.QtWidgets import QWidget
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'refresh_theme') and callable(widget.refresh_theme):
                try: 
                    widget.refresh_theme()
                except Exception as e: 
                    logger.debug(f"Silent skip refresh on {widget.__class__.__name__}: {e}")

        # 2. Refresco de Layout: Forzar re-pintado de contenedores principales
        if hasattr(self, 'identity_banner'): self.identity_banner.refresh_theme()
        
        # Polishing final para asegurar que QSS se aplique a todos
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _on_repair_vault_dashboard(self):
        """Lanza el menú avanzado de Integridad y Herramientas de Recuperación."""
        from src.presentation.dialogs.recovery_dialog import VaultRepairDialog, OrphanRescueDialog
        from src.presentation.dialogs.shadow_vault_dialog import ShadowVaultDialog
        from src.presentation.ui_utils import PremiumMessage
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        
        if not self.sm or not self.current_username:
            PremiumMessage.warning(self, "Error", "No hay sesión activa para reparar.")
            return

        # --- MENÚ TÁCTICO DE INTEGRIDAD ---
        msg = QDialog(self)
        msg.setWindowTitle("🛡️ Herramientas de Integridad y Rescate")
        msg.setFixedWidth(500)
        l = QVBoxLayout(msg)
        l.setContentsMargins(30, 30, 30, 30); l.setSpacing(15)
        
        lbl = QLabel("<h2>Diagnóstico de Bóveda</h2>Seleccione la operación de mantenimiento:")
        lbl.setObjectName("repair_dialog_title")
        l.addWidget(lbl)
        
        # Opción 1: Shadow Vault (Lo nuevo)
        btn_shadow = QPushButton(MESSAGES.REPAIR.BTN_SHADOW)
        btn_shadow.setObjectName("repair_action_btn"); btn_shadow.setProperty("btn_type", "ai_sec")
        btn_shadow.clicked.connect(lambda: msg.done(10))
        l.addWidget(btn_shadow)
        
        # Opción 2: Orphans
        btn_orphans = QPushButton(MESSAGES.REPAIR.BTN_ORPHANS)
        btn_orphans.setObjectName("repair_action_btn"); btn_orphans.setProperty("btn_type", "primary")
        btn_orphans.clicked.connect(lambda: msg.done(20))
        l.addWidget(btn_orphans)
        
        # Opción 3: Access Repair
        btn_repair = QPushButton(MESSAGES.REPAIR.BTN_ACCESS)
        btn_repair.setObjectName("repair_action_btn"); btn_repair.setProperty("btn_type", "danger")
        btn_repair.clicked.connect(lambda: msg.done(30))
        l.addWidget(btn_repair)
        
        btn_cancel = QPushButton(MESSAGES.COMMON.BTN_NO)
        btn_cancel.setObjectName("repair_cancel_btn")
        btn_cancel.clicked.connect(msg.reject)
        l.addWidget(btn_cancel)
        
        choice = msg.exec_()

        if choice == 10:
            # Explorador de Sombras
            dialog = ShadowVaultDialog(self.sm, self.sync_manager, self)
            dialog.exec_()
            self._force_full_sync() 
            
        elif choice == 20:
            # Rescate de Huérfanos
            dialog = OrphanRescueDialog(self.current_username, self.user_manager, self)
            dialog.exec_()
            self._force_full_sync() 
            
        elif choice == 30:
            # Reparación de Llaves
            dialog = VaultRepairDialog(self.current_username, self.sm, self)
            if dialog.exec_():
                PremiumMessage.information(self, MESSAGES.COMMON.TITLE_RESTART, MESSAGES.COMMON.MSG_RESTART)
                self.close()

    def _force_full_sync(self):
        self._on_sync()
        self._load_table()

    def _on_sync_audit(self):
        """Sincroniza el historial con la nube de forma manual."""
        try:
            self.sync_manager.sync_audit_logs()
            self._load_table_audit()
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.success(self, "Historial Sincronizado", "Los registros de la nube han sido integrados con el historial local.")
        except Exception as e:
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.error(self, "Error de Sincronización", str(e))
    def _on_rotate_bulk(self):
        """Dispara el menú de mantenimiento y rotación masiva."""
        self._on_repair_vault_dashboard()

    def _on_add_user_global(self):
        """Acceso rápido a la gestión de usuarios."""
        from src.presentation.user_management_dialog import UserManagementDialog
        dlg = UserManagementDialog(self.user_manager, self.current_username, parent=self)
        dlg.exec_()

    def _on_dash_search_return(self):
        """Protocolo de búsqueda rápida: Salta al Vault y filtra instantáneamente."""
        text = self.dash_search.text().strip()
        if not text: return
        
        # 1. Transición Visual al Vault
        if hasattr(self, 'view_vault'):
            self.main_stack.setCurrentWidget(self.view_vault)
            if hasattr(self, 'btn_nav_vault'): self.btn_nav_vault.setChecked(True)
            
        # 2. Inyección de búsqueda y foco táctico
        target = None
        # HUD Search Priority
        if hasattr(self, 'dash_search'):
            target = self.dash_search
        elif hasattr(self, 'search_vault'):
            target = self.search_vault
        
        if target:
            target.setText(text)
            target.setFocus()
            target.selectAll()
            
        # 3. Limpiar puente de búsqueda
        self.dash_search.clear()

    def _toggle_voice_search(self):
        if self.voice_worker.isRunning():
            return
        
        # 1. Limpiar campo inmediatamente
        if hasattr(self, 'search_vault'):
            self.search_vault.clear()
            
        # 2. Iniciar trabajador
        self.voice_worker.start()

    def _on_voice_listening_started(self):
        # 3. Feedback Sonoro (Windows Beep táctico)
        try:
            winsound.Beep(1000, 150) # Tono agudo y corto
        except: pass
        
        self.btn_voice_search.setProperty("listening", "true")
        self.btn_voice_search.style().unpolish(self.btn_voice_search)
        self.btn_voice_search.style().polish(self.btn_voice_search)
        self.btn_voice_search.setText("🛑")
        if hasattr(self, 'search_vault'):
            self.search_vault.setPlaceholderText("Listening... speak now 🎤")

    def _on_voice_listening_finished(self):
        self.btn_voice_search.setProperty("listening", "false")
        self.btn_voice_search.style().unpolish(self.btn_voice_search)
        self.btn_voice_search.style().polish(self.btn_voice_search)
        self.btn_voice_search.setText("🎤")
        if hasattr(self, 'search_vault'):
            self.search_vault.setPlaceholderText("🔍 Search credentials...")

    def _on_voice_search_result(self, text):
        if hasattr(self, 'search_vault'):
            self.search_vault.setText(text)
            # El evento textChanged ya disparará el filtrado
            logger.info(f"Voice Search success: {text}")

    def _on_voice_search_error(self, error_msg):
        from src.presentation.notifications.notification_manager import Notifications
        Notifications.show_toast(self, "Voice Search", error_msg, icon="❌", accent_color="#ef4444")
        logger.error(f"Voice Search error: {error_msg}")

    def closeEvent(self, event):
        """
        PROTOCOLO DE CIERRE SEGURO:
        - Detiene el Vigilante Global.
        - Detiene trabajadores de red y heurística.
        - Notifica al servidor el cierre de sesión.
        """
        logger.info("Executing Secure Close Protocol...")
        
        if hasattr(self, "watcher"): self.watcher.stop()
        
        # Detener trabajadores asíncronos
        try:
            if hasattr(self, "conn_worker"): self.conn_worker.stop()
            if hasattr(self, "heuristic_worker"): self.heuristic_worker.running = False
            if hasattr(self, "voice_worker"): self.voice_worker.terminate() # Force stop audio
        except: pass

        # Notificar Logout Remoto (Heartbeat Final)
        try:
            if hasattr(self, 'sync_manager'):
                self.sync_manager.send_heartbeat(action="LOGOUT", status="OFFLINE")
        except: pass
        
        logger.info("Vault closed correctly.")
        event.accept()
