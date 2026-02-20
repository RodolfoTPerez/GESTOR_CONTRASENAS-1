from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QLabel, QPushButton, QComboBox, QFrame
)
import logging
from PyQt5.QtCore import Qt
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.dialogs.recovery_dialog import VaultRepairDialog

from src.presentation.theme_manager import ThemeManager
from src.presentation.notifications.notification_manager import Notifications

class SettingsDialog(QDialog):
    def __init__(self, settings=None, guardian_ai=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.guardian_ai = guardian_ai
        self.logger = logging.getLogger(__name__)
        self.theme = ThemeManager()
        
        # Sincronizar tema ANTES de mostrar para evitar destellos
        # [SENIOR FIX] Use Correct Global Scope
        if not self.settings:
             from PyQt5.QtCore import QSettings
             self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")

        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        self.setWindowTitle(MESSAGES.SETTINGS.TITLE_WINDOW)
        self.setFixedSize(850, 520)

        # [THEME FIX] Wrapper Strategy for Windows Dialogs
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        
        self.frame = QFrame()
        self.frame.setObjectName("DialogFrame")
        self.frame.setAttribute(Qt.WA_StyledBackground, True)
        
        # [DEBUG] Confirm color
        colors = self.theme.get_theme_colors()
        self.logger.debug(f"Theme BG: {colors.get('bg', 'UNKNOWN')}")
        
        wrapper_layout.addWidget(self.frame)

        # Apply generic dialog styles (Now includes #DialogFrame rules)
        # [SENIOR FIX] Force Glass Effect on inner cards by overriding the solid token
        # We manually calculate RGBA for the card background to ensure transparency
        card_bg_hex = colors.get("bg_dashboard_card", "#0f172a")
        if card_bg_hex.startswith("#"):
             c_bg = QColor(card_bg_hex)
             glass_bg = f"rgba({c_bg.red()}, {c_bg.green()}, {c_bg.blue()}, 0.95)"
        else: glass_bg = card_bg_hex

        base_qss = self.theme.load_stylesheet("dialogs")
        self.setStyleSheet(self.theme.apply_tokens(base_qss + f"""
            QFrame#card {{
                background-color: {glass_bg};
                border: 1px solid @border;
                border-radius: @border-radius-main;
            }}
        """))

        main_v_layout = QVBoxLayout(self.frame)
        main_v_layout.setContentsMargins(30, 30, 30, 30)
        main_v_layout.setSpacing(25)

        # HEADER
        header_lbl = QLabel(MESSAGES.SETTINGS.HEADER)
        header_lbl.setObjectName("section_title")
        main_v_layout.addWidget(header_lbl)

        # HORIZONTAL CONTENT SECTION
        content_h_layout = QHBoxLayout()
        content_h_layout.setSpacing(25)
 
        # --- COLUMNA IZQUIERDA: GENERAL ---
        left_card = QFrame()
        left_card.setObjectName("card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)
 
        left_layout.addWidget(QLabel(MESSAGES.SETTINGS.LBL_GENERAL, objectName="dialog_subtitle"))

        # [NEW] THEME SELECTOR - CRITICAL FIX
        left_layout.addWidget(QLabel(MESSAGES.SETTINGS.LBL_THEME))
        self.combo_theme = QComboBox()
        
        # Populate with themes
        themes = self.theme.THEMES
        # Add formatted items: "Name (id)" or just Name and store ID as user data
        for t_id, t_data in themes.items():
            self.combo_theme.addItem(t_data["name"], t_id)
            
        # Select current theme
        curr_theme = self.settings.value("theme_active", "tactical_dark")
        idx = self.combo_theme.findData(curr_theme)
        if idx >= 0: self.combo_theme.setCurrentIndex(idx)
        else: self.combo_theme.setCurrentIndex(0)
            
        left_layout.addWidget(self.combo_theme)

        left_layout.addWidget(QLabel(MESSAGES.SETTINGS.LBL_TIMEOUT))
        self.combo_timeout = QComboBox()
        self.combo_timeout.addItems(["1 Minute", "5 Minutes", "10 Minutes", "30 Minutes", "60 Minutes"])
        
        # [SENIOR FIX] Load from user-specific settings
        saved_timeout = self.settings.value("auto_lock_time", 10, type=int)
        
        # Mapeo inverso para seleccionar el item correcto
        timeout_map = {1: 0, 5: 1, 10: 2, 30: 3, 60: 4}
        self.combo_timeout.setCurrentIndex(timeout_map.get(saved_timeout, 2))
        
        left_layout.addWidget(self.combo_timeout)

        left_layout.addWidget(QLabel(MESSAGES.SETTINGS.LBL_LANG))
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Español (ES)", "ES")
        self.combo_lang.addItem("English (EN)", "EN")
        current_lang = MESSAGES.LANG
        idx = self.combo_lang.findData(current_lang)
        self.combo_lang.setCurrentIndex(idx if idx >= 0 else 0)
        left_layout.addWidget(self.combo_lang)

        left_layout.addWidget(QLabel(MESSAGES.SETTINGS.LBL_VAULT_NAME))
        
        vault_name_layout = QHBoxLayout()
        vault_name_layout.setSpacing(10)
        
        self.input_instance_name = QLineEdit()
        self.input_instance_name.setReadOnly(True) # Read-only by default
        instance_name = ""
        if hasattr(self.parent(), 'sm'):
            instance_name = self.parent().sm.get_meta("instance_name") or "VULTRAX CORE"
        self.original_instance_name = instance_name # [OPTIMIZATION] Store for diff check
        self.input_instance_name.setText(instance_name)
        
        self.btn_modify_name = QPushButton(MESSAGES.SETTINGS.BTN_MOD)
        self.btn_modify_name.setObjectName("btn_secondary")
        self.btn_modify_name.setFixedWidth(100)
        self.btn_modify_name.setCursor(Qt.PointingHandCursor)
        self.btn_modify_name.clicked.connect(self._enable_instance_name_edit)
        
        vault_name_layout.addWidget(self.input_instance_name)
        vault_name_layout.addWidget(self.btn_modify_name)
        
        left_layout.addLayout(vault_name_layout)

        left_layout.addStretch()
        
        # New Repair Button
        # New Repair Button (HIGH VISIBILITY)
        repair_btn = QPushButton(MESSAGES.SETTINGS.BTN_REPAIR)
        repair_btn.setObjectName("btn_danger")
        repair_btn.setCursor(Qt.PointingHandCursor)
        repair_btn.clicked.connect(self._open_vault_repair)
        left_layout.addWidget(repair_btn)
        
        sync_lbl = QLabel(MESSAGES.SETTINGS.LBL_SYNC_ACTIVE)
        colors = self.theme.get_theme_colors()
        sync_lbl.setStyleSheet(f"color: {colors['success']}; font-weight: 800; font-size: 11px;")
        left_layout.addWidget(sync_lbl)

        content_h_layout.addWidget(left_card, stretch=1)

        # --- COLUMNA DERECHA: INTELIGENCIA ESTRATÉGICA (IA) ---
        ai_card = QFrame()
        ai_card.setObjectName("card")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setContentsMargins(25, 25, 25, 25)
        ai_layout.setSpacing(18)
 
        # Header
        ai_header = QLabel("🧠 " + MESSAGES.SETTINGS.LBL_API_KEYS)
        ai_header.setObjectName("dialog_subtitle")
        ai_layout.addWidget(ai_header)
        
        # Provider Selector Section
        provider_section = QHBoxLayout()
        provider_section.setSpacing(12)
        
        provider_label = QLabel(MESSAGES.SETTINGS.LBL_AI_ENGINE)
        provider_label.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["Disabled", "Google Gemini ✨", "OpenAI ChatGPT 🤖", "Anthropic Claude 🛡️"])
        self.combo_provider.setMinimumWidth(220)
        saved_provider = self.settings.value("ai_provider_active", "Disabled")
        idx = self.combo_provider.findText(saved_provider)
        if idx >= 0: self.combo_provider.setCurrentIndex(idx)
        self.combo_provider.currentIndexChanged.connect(self._on_provider_changed)
        
        provider_section.addWidget(provider_label)
        provider_section.addWidget(self.combo_provider)
        provider_section.addStretch()
        ai_layout.addLayout(provider_section)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {colors['border']}; max-height: 1px;")
        ai_layout.addWidget(separator)
        
        # API Keys Section
        keys_label = QLabel("API Keys (Las 3 se guardan simultáneamente)")
        keys_label.setObjectName("dialog_subtitle")
        keys_label.setStyleSheet(f"color: {colors['text_dim']}; font-size: 11px;")
        ai_layout.addWidget(keys_label)
        
        # Gemini Key
        gemini_layout = QVBoxLayout()
        gemini_layout.setSpacing(6)
        gemini_header = QHBoxLayout()
        self.lbl_gemini = QLabel("Google Gemini")
        self.lbl_gemini.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        self.status_gemini = QLabel()
        gemini_header.addWidget(self.lbl_gemini)
        gemini_header.addWidget(self.status_gemini)
        gemini_header.addStretch()
        gemini_layout.addLayout(gemini_header)
        
        self.input_key_gemini = QLineEdit()
        self.input_key_gemini.setPlaceholderText("AIza...")
        self.input_key_gemini.setEchoMode(QLineEdit.Password)
        self.input_key_gemini.setText(self.settings.value("ai_key_gemini", ""))
        self.input_key_gemini.textChanged.connect(self._update_status_indicators)
        gemini_layout.addWidget(self.input_key_gemini)
        ai_layout.addLayout(gemini_layout)
        
        # ChatGPT Key
        chatgpt_layout = QVBoxLayout()
        chatgpt_layout.setSpacing(6)
        chatgpt_header = QHBoxLayout()
        self.lbl_chatgpt = QLabel("OpenAI ChatGPT")
        self.lbl_chatgpt.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        self.status_chatgpt = QLabel()
        chatgpt_header.addWidget(self.lbl_chatgpt)
        chatgpt_header.addWidget(self.status_chatgpt)
        chatgpt_header.addStretch()
        chatgpt_layout.addLayout(chatgpt_header)
        
        self.input_key_chatgpt = QLineEdit()
        self.input_key_chatgpt.setPlaceholderText("sk-...")
        self.input_key_chatgpt.setEchoMode(QLineEdit.Password)
        self.input_key_chatgpt.setText(self.settings.value("ai_key_chatgpt", ""))
        self.input_key_chatgpt.textChanged.connect(self._update_status_indicators)
        chatgpt_layout.addWidget(self.input_key_chatgpt)
        ai_layout.addLayout(chatgpt_layout)
        
        # Claude Key
        claude_layout = QVBoxLayout()
        claude_layout.setSpacing(6)
        claude_header = QHBoxLayout()
        self.lbl_claude = QLabel("Anthropic Claude")
        self.lbl_claude.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        self.status_claude = QLabel()
        claude_header.addWidget(self.lbl_claude)
        claude_header.addWidget(self.status_claude)
        claude_header.addStretch()
        claude_layout.addLayout(claude_header)
        
        self.input_key_claude = QLineEdit()
        self.input_key_claude.setPlaceholderText("sk-ant-...")
        self.input_key_claude.setEchoMode(QLineEdit.Password)
        self.input_key_claude.setText(self.settings.value("ai_key_claude", ""))
        self.input_key_claude.textChanged.connect(self._update_status_indicators)
        claude_layout.addWidget(self.input_key_claude)
        ai_layout.addLayout(claude_layout)
        
        # Info footer
        info_lbl = QLabel("🔒 " + MESSAGES.SETTINGS.LBL_LOCAL_ENC_INFO)
        info_lbl.setObjectName("dialog_subtitle")
        info_lbl.setStyleSheet(f"color: {colors['text_dim']}; font-size: 10px; margin-top: 8px;")
        info_lbl.setWordWrap(True)
        ai_layout.addWidget(info_lbl)

        content_h_layout.addWidget(ai_card, stretch=2)
        
        # Initialize status indicators
        self._update_status_indicators()

        main_v_layout.addLayout(content_h_layout)

        # --- BOTONES DE ACCIÓN ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton(MESSAGES.SETTINGS.BTN_CANCEL)
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.setFixedWidth(150)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton(MESSAGES.SETTINGS.BTN_SAVE)
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setFixedWidth(250)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        main_v_layout.addLayout(btn_layout)

    def refresh_theme(self):
        """NUCLEAR THEME REFRESH: Re-applies all dynamic tokens."""
        # This is critical for Glass/Tactical switching
        colors = self.theme.get_theme_colors()
        
        # 1. Update card backgrounds (Glass vs Solid)
        card_bg_hex = colors.get("bg_dashboard_card", "#0f172a")
        if card_bg_hex.startswith("#"):
             c_bg = QColor(card_bg_hex)
             glass_bg = f"rgba({c_bg.red()}, {c_bg.green()}, {c_bg.blue()}, 0.95)"
        else: glass_bg = card_bg_hex

        base_qss = self.theme.load_stylesheet("dialogs")
        self.setStyleSheet(self.theme.apply_tokens(base_qss + f"""
            QFrame#card {{
                background-color: {glass_bg};
                border: 1px solid @border;
                border-radius: @border-radius-main;
            }}
        """))
        
        # 2. Update specific labels that use manual colors (like headers)
        self.lbl_gemini.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        self.lbl_chatgpt.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        self.lbl_claude.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        
        self._update_status_indicators()
    
    def _update_status_indicators(self):
        """Update visual status indicators for API keys."""
        colors = self.theme.get_theme_colors()
        
        # Get current provider
        current_provider = self.combo_provider.currentText()
        
        # Check which keys are configured
        has_gemini = bool(self.input_key_gemini.text().strip())
        has_chatgpt = bool(self.input_key_chatgpt.text().strip())
        has_claude = bool(self.input_key_claude.text().strip())
        
        # Update Gemini status
        if "Gemini" in current_provider:
            self.status_gemini.setText(f"<span style='color: {colors['primary']}; font-weight: 800;'>● ACTIVO</span>")
            self.lbl_gemini.setStyleSheet(f"font-weight: 800; color: {colors['primary']};")
        elif has_gemini:
            self.status_gemini.setText(f"<span style='color: {colors['success']}; font-weight: 600;'>✓ Configurada</span>")
            self.lbl_gemini.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        else:
            self.status_gemini.setText(f"<span style='color: {colors['text_dim']}; font-weight: 400;'>⚠ Sin configurar</span>")
            self.lbl_gemini.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        
        # Update ChatGPT status
        if "ChatGPT" in current_provider:
            self.status_chatgpt.setText(f"<span style='color: {colors['primary']}; font-weight: 800;'>● ACTIVO</span>")
            self.lbl_chatgpt.setStyleSheet(f"font-weight: 800; color: {colors['primary']};")
        elif has_chatgpt:
            self.status_chatgpt.setText(f"<span style='color: {colors['success']}; font-weight: 600;'>✓ Configurada</span>")
            self.lbl_chatgpt.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        else:
            self.status_chatgpt.setText(f"<span style='color: {colors['text_dim']}; font-weight: 400;'>⚠ Sin configurar</span>")
            self.lbl_chatgpt.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        
        # Update Claude status
        if "Claude" in current_provider:
            self.status_claude.setText(f"<span style='color: {colors['primary']}; font-weight: 800;'>● ACTIVO</span>")
            self.lbl_claude.setStyleSheet(f"font-weight: 800; color: {colors['primary']};")
        elif has_claude:
            self.status_claude.setText(f"<span style='color: {colors['success']}; font-weight: 600;'>✓ Configurada</span>")
            self.lbl_claude.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
        else:
            self.status_claude.setText(f"<span style='color: {colors['text_dim']}; font-weight: 400;'>⚠ Sin configurar</span>")
            self.lbl_claude.setStyleSheet(f"font-weight: 600; color: {colors['text']};")
    
    def _on_provider_changed(self):
        """Handle provider selection change."""
        self._update_status_indicators()

    def _on_save(self):
        provider = self.combo_provider.currentText()
        new_theme = self.combo_theme.currentData()
        
        key_gemini = self.input_key_gemini.text().strip()
        key_chatgpt = self.input_key_chatgpt.text().strip()
        key_claude = self.input_key_claude.text().strip()
        
        # [THEME APPLIER] Instant switch
        if new_theme:
            self.settings.setValue("theme_active", new_theme)
            self.theme.set_theme(new_theme)
            
            # Force Application-Wide Polish
            from PyQt5.QtWidgets import QApplication
            self.theme.apply_app_theme(QApplication.instance())
            self.logger.info(f"Theme switched to: {new_theme}")
            
        old_lang = MESSAGES.LANG
        selected_lang = self.combo_lang.currentData()
        
        # Bloqueo (Mapeo Robusto)
        timeout_text = self.combo_timeout.currentText()
        # [THEME FIX] Language-agnostic logic
        if "1 " in timeout_text: lock_val = 1
        elif "5 " in timeout_text: lock_val = 5
        elif "10 " in timeout_text: lock_val = 10
        elif "30 " in timeout_text: lock_val = 30
        elif "60 " in timeout_text or "1 H" in timeout_text or "1 h" in timeout_text: lock_val = 60
        else: lock_val = 10
        
        # [SENIOR FIX] Guardar en el scope del USUARIO actual
        old_lock = self.settings.value("auto_lock_time", 10, type=int)
        self.settings.setValue("auto_lock_time", lock_val)
        self.settings.sync() # Forzar persistencia física
        
        if lock_val != old_lock:
            Notifications.show_toast(self, "Protocolo de Seguridad", f"Inactividad ajustada a {lock_val} min.", "⏲️", "#f59e0b")
        
        # [LIVE UPDATE] Sincronizar el Watcher y la UI del Dashboard (Nuclear Sync)
        try:
            from src.presentation.inactivity_watcher import GlobalInactivityWatcher
            watcher = GlobalInactivityWatcher.get_instance(lock_val * 60 * 1000)
            
            # Si el padre es el Dashboard, forzar su refresco visual
            parent = self.parent()
            if hasattr(parent, '_init_watcher'):
                parent._init_watcher()
            elif hasattr(parent, 'parent') and hasattr(parent.parent(), '_init_watcher'):
                # DashboardActions es un mixin, el parent real suele ser DashboardView
                parent.parent()._init_watcher()
                
            self.logger.info(f"Nuclear Sync Triggered: {lock_val} min")
        except Exception as e:
            self.logger.error(f"Failed to update watcher: {e}")
            
        self.settings.setValue("ai_provider_active", provider)
        self.settings.setValue("ai_key_gemini", key_gemini)
        self.settings.setValue("ai_key_chatgpt", key_chatgpt)
        self.settings.setValue("ai_key_claude", key_claude)
        self.settings.setValue("language", selected_lang)
        
        # [SENIOR FIX] Force GLOBAL persistence for Language & Theme using INI for maximum reliability
        try:
            from PyQt5.QtCore import QSettings
            from src.infrastructure.config.path_manager import PathManager
            config_path = str(PathManager.GLOBAL_SETTINGS_INI)
            global_settings = QSettings(config_path, QSettings.IniFormat)
            global_settings.setValue("language", selected_lang)
            
            # [FIX] Always verify current effective theme if new_theme is None
            final_theme = new_theme if new_theme else self.theme.current_theme
            global_settings.setValue("theme_active", final_theme)
            
            global_settings.sync()
            self.logger.info(f"Global INI Sync: Language='{selected_lang}', Theme='{final_theme}'")
            self.logger.debug(f"INI Path: {config_path}")
        except Exception as e:
            self.logger.error(f"Could not save global INI: {e}")

        # Actualizar mensajes
        MESSAGES.LANG = selected_lang
        
        if hasattr(self.parent(), 'sm'):
            sm = self.parent().sm
            sm.set_meta("language", selected_lang)
            
            # Gestionar Nombre de Bóveda
            new_name = self.input_instance_name.text().strip()
            
            # [OPTIMIZATION] Only trigger network sync if name CHANGED
            original_name = getattr(self, "original_instance_name", "VULTRAX CORE")
            
            if new_name and new_name != original_name:
                sm.set_meta("instance_name", new_name)
                # Intentar sincronizar con la nube
                try:
                    from src.infrastructure.user_manager import UserManager
                    um = UserManager(sm)
                    v_id = sm.get_meta("vault_id")
                    if v_id:
                        um.sync_vault_name(v_id, new_name)
                except Exception as e:
                    self.logger.error(f"Error syncing vault name: {e}")

            # [OPTIMIZATION] Skip expensive retranslateUi since we ask for Restart anyway
            # if hasattr(self.parent(), 'retranslateUi'): self.parent().retranslateUi()
        
        # Re-configurar motor Guardian AI en tiempo real
        active_key = ""
        if "Gemini" in provider: active_key = key_gemini
        elif "ChatGPT" in provider: active_key = key_chatgpt
        elif "Claude" in provider: active_key = key_claude
        
        self.guardian_ai.configure_engine(provider, active_key)
        
        # [UX] Notificación inteligente
        if selected_lang != old_lang:
            PremiumMessage.information(self, MESSAGES.SETTINGS.MSG_RESTART_NEEDED, 
                MESSAGES.SETTINGS.MSG_RESTART_TEXT)
        else:
            PremiumMessage.success(self, MESSAGES.SETTINGS.MSG_SAVED_TITLE, 
                MESSAGES.SETTINGS.MSG_SAVED_TEXT.format(provider=provider))

        self.accept()

    def _open_vault_repair(self):
        """Abre el diálogo de reparación de llaves encriptadas."""
        # Necesitamos el secrets_manager del padre (MainWindow o Dashboard)
        sm = None
        if hasattr(self.parent(), 'sm'):
             sm = self.parent().sm
        
        if not sm or not sm.current_user:
            PremiumMessage.warning(self, "Error", "No se puede reparar sin una sesión de usuario cargada.")
            return

        dialog = VaultRepairDialog(sm.current_user, sm, self)
        if dialog.exec_() == QDialog.Accepted:
            # Si tuvo éxito, cerramos Settings también para forzar flow limpio
            self.accept()

    def _enable_instance_name_edit(self):
        """Habilita la edición del nombre de la instancia."""
        self.input_instance_name.setReadOnly(False)
        self.input_instance_name.setFocus()
        self.btn_modify_name.setEnabled(False)
        self.btn_modify_name.setText("OK")
