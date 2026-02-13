import logging
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QWidget, QDialog, QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt
from src.domain.messages import MESSAGES
# Use absolute imports to avoid circular and path issues
from src.presentation.theme_manager import ThemeManager
from src.presentation.ui_utils import PremiumMessage
from src.presentation.widgets.glass_card import GlassCard
from src.presentation.user_management_dialog import UserManagementDialog
from src.presentation.sessions_dialog import SessionsDialog
from src.presentation.two_factor_setup_dialog import TwoFactorSetupDialog

logger = logging.getLogger(__name__)

class AdminPanel(QWidget):
    """
    Componente modular del Panel de Administración.
    Centraliza la gestión de usuarios, sesiones y mantenimiento de núcleo.
    """
    def __init__(self, sm, um, sync_manager, current_username, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.um = um
        self.sync_manager = sync_manager
        self.current_username = current_username
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        # Match Settings Page margins/spacing exactly
        main_layout.setContentsMargins(50, 40, 50, 70)
        main_layout.setSpacing(25)

        # Standard Page Hierarchy
        self.setObjectName("settings_page")

        # Header - Matches #settings_title in QSS
        h = QHBoxLayout()
        title_text = MESSAGES.ADMIN.TITLE_PROTOCOL.upper() if hasattr(MESSAGES, 'ADMIN') else 'ADMIN PROTOCOL'
        t = QLabel(f"👥 {title_text}")
        t.setObjectName("settings_title")
        h.addWidget(t)
        h.addStretch()
        main_layout.addLayout(h)
        main_layout.addSpacing(15)

        def add_command_row(layout, icon, title, subtitle, btn_obj, btn_text, color_key):
            # No hardcoded styles here - rely on QSS and theme variables
            row_layout = QHBoxLayout()
            row_layout.setSpacing(15)
            
            # Content Info (Title + Desc)
            info_v = QVBoxLayout()
            info_v.setSpacing(4)
            
            l_tit = QLabel(f"{icon} {title}")
            l_tit.setObjectName("settings_label")
            
            l_sub = QLabel(subtitle)
            l_sub.setObjectName("settings_desc")
            
            info_v.addWidget(l_tit)
            info_v.addWidget(l_sub)
            
            row_layout.addLayout(info_v)
            row_layout.addStretch()
            
            btn_obj.setText(btn_text if btn_text else "ACTION")
            btn_obj.setCursor(Qt.PointingHandCursor)
            btn_obj.setFixedWidth(150)
            btn_obj.setObjectName("btn_settings_action") # Match settings button style
            btn_obj.setProperty("btn_type", color_key)
            
            row_layout.addWidget(btn_obj)
            layout.addLayout(row_layout)

        # Helper to create transparent headers
        def add_section_header(layout, icon, text):
            lbl = QLabel(f"{icon} {text}")
            lbl.setObjectName("settings_category_label")
            layout.addWidget(lbl)

        # --- CATEGORY 1: AUTHORITY & IDENTITY ---
        add_section_header(main_layout, "🔐", MESSAGES.ADMIN.CAT_IDENTITY)
        
        card_id = GlassCard()
        card_id.setProperty("depth", "settings")
        # card_id.setProperty("ghost", "true") # Usually not needed if depth is settings
        l_id = QVBoxLayout(card_id)
        # Match Settings Card margins
        l_id.setContentsMargins(30, 25, 30, 25)
        l_id.setSpacing(18)
        
        self.btn_manage_users = QPushButton()
        add_command_row(l_id, "👥", MESSAGES.ADMIN.NODES_ACCESS, MESSAGES.ADMIN.DESC_NODES, self.btn_manage_users, MESSAGES.ADMIN.BTN_MODIFY, "primary")
        
        self.btn_sessions = QPushButton()
        add_command_row(l_id, "📡", MESSAGES.ADMIN.MONITOR_OPS, MESSAGES.ADMIN.DESC_MONITOR, self.btn_sessions, MESSAGES.ADMIN.BTN_OPEN, "accent")
        
        main_layout.addWidget(card_id)

        # --- CATEGORY 2: CORE MAINTENANCE ---
        add_section_header(main_layout, "🛠️", MESSAGES.ADMIN.CAT_CORE)
        
        card_sec = GlassCard()
        card_sec.setProperty("depth", "settings")
        l_sec = QVBoxLayout(card_sec)
        l_sec.setContentsMargins(30, 25, 30, 25)
        l_sec.setSpacing(18)
        
        self.btn_regenerate_2fa = QPushButton()
        add_command_row(l_sec, "🔐", MESSAGES.ADMIN.ROTATION_TOTP, MESSAGES.ADMIN.DESC_TOTP, self.btn_regenerate_2fa, MESSAGES.ADMIN.BTN_ROTATE, "primary")
        
        self.btn_clean_local = QPushButton()
        add_command_row(l_sec, "🧹", MESSAGES.ADMIN.DEBUG_DB, MESSAGES.ADMIN.DESC_DEBUG, self.btn_clean_local, MESSAGES.ADMIN.BTN_EMPTY, "success")
        
        main_layout.addWidget(card_sec)

        # --- CATEGORY 3: EXCLUSION ZONE ---
        add_section_header(main_layout, "⚠️", MESSAGES.ADMIN.CAT_ZONE)
        
        card_danger = GlassCard()
        card_danger.setProperty("depth", "settings")
        l_danger = QVBoxLayout(card_danger)
        l_danger.setContentsMargins(30, 25, 30, 25)
        l_danger.setSpacing(18)
        
        self.btn_purge = QPushButton()
        add_command_row(l_danger, "☢️", MESSAGES.ADMIN.REMOTE_PURGE, MESSAGES.ADMIN.DESC_PURGE, self.btn_purge, MESSAGES.ADMIN.BTN_EXECUTE, "danger")
        
        main_layout.addWidget(card_danger)
        main_layout.addStretch()

    def _connect_signals(self):
        self.btn_manage_users.clicked.connect(self._on_manage_users)
        self.btn_sessions.clicked.connect(self._on_sessions)
        self.btn_regenerate_2fa.clicked.connect(self._on_regenerate_2fa)
        self.btn_clean_local.clicked.connect(self._on_clean_local)
        self.btn_purge.clicked.connect(self._on_purge_remote)

    # --- ACTION HANDLERS (Extracted from DashboardActions) ---

    def _on_manage_users(self):
        dlg = UserManagementDialog(self.um, self.current_username, self)
        dlg.exec_()

    def _on_sessions(self):
        dlg = SessionsDialog(self.sync_manager, current_username=self.current_username, parent=self)
        dlg.exec_()

    def _on_regenerate_2fa(self):
        if not PremiumMessage.question(
            self, 
            MESSAGES.TWOFACTOR.TITLE_REGENERATE,
            MESSAGES.TWOFACTOR.TEXT_CONFIRM_REGEN + "\n\n" + MESSAGES.DASHBOARD.AUDIT_DIAGNOSTIC
        ):
            return
        
        # Access master password if available in parent/global context
        # In the original, it was checked on the dashboard instance
        master_pwd = getattr(self.parent(), 'master_password', None)
        if master_pwd:
            self.sm.last_password = master_pwd

        dlg = TwoFactorSetupDialog(self.um, self.sm, self.current_username, self)
        if dlg.exec_() == QDialog.Accepted:
            self.sm.log_event("REGEN_2FA", details="Token de seguridad regenerado")
            PremiumMessage.success(self, MESSAGES.TWOFACTOR.TITLE_REGENERATE, MESSAGES.TWOFACTOR.SUCCESS_REGEN)
        else:
            logger.info("User canceled 2FA regeneration.")

    def _on_clean_local(self):
        if not PremiumMessage.question(
            self, 
            MESSAGES.DASHBOARD.TITLE_CLEAN_LOCAL, 
            MESSAGES.DASHBOARD.TEXT_CLEAN_LOCAL_CONFIRM
        ):
            return
        try:
            self.sm.clear_local_secrets()
            # We need to refresh the table in the dashboard
            if hasattr(self.parent(), '_load_table'):
                self.parent()._load_table()
            self.sm.log_event("ADMIN_DB_CLEAN", details="Mantenimiento de base de datos local completado.")
            PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_CLEAN_LOCAL, MESSAGES.DASHBOARD.TEXT_CLEAN_LOCAL_SUCCESS)
        except Exception as e:
            PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, str(e))

    def _on_purge_remote(self):
        # 1. Advertencia Crítica
        if not PremiumMessage.question(self, MESSAGES.ADMIN.TITLE_PURGE, MESSAGES.ADMIN.TEXT_PURGE_WARN): 
            return
        
        # 2. Re-verificación de Seguridad (Password)
        pwd, ok = QInputDialog.getText(self, MESSAGES.ADMIN.TITLE_AUTH_L1, 
                                     MESSAGES.ADMIN.TEXT_AUTH_L1, 
                                     QLineEdit.Password)
        if not ok or not pwd:
            return

        # 3. FRICCIÓN EXTREMA (Confirmación por palabra clave)
        expected_keyword = MESSAGES.ADMIN.KEYWORD_CONFIRM
        confirm_text, ok = QInputDialog.getText(self, MESSAGES.ADMIN.TITLE_AUTH_L2, 
                                              MESSAGES.ADMIN.TEXT_AUTH_L2)
        if not ok or confirm_text != expected_keyword:
            PremiumMessage.info(self, MESSAGES.ADMIN.MSG_ABORTED, MESSAGES.ADMIN.TEXT_ABORTED)
            return

        # 4. Validar contra el perfil local
        profile = self.um.sm.get_local_user_profile(self.current_username)
        if not profile:
             u_data = self.um.validate_user_access(self.current_username)
             profile = u_data if u_data and u_data.get("exists") else None

        if not profile or not self.um.verify_password(pwd, profile["salt"], profile["password_hash"]):
            PremiumMessage.error(self, MESSAGES.ADMIN.MSG_DENIED, MESSAGES.ADMIN.TEXT_DENIED)
            return

        # 4. Ejecución del comando de purga
        try:
            self.sync_manager.purge_all_remote_data()
            self.sm.clear_local_secrets()
            if hasattr(self.parent(), '_load_table'):
                self.parent()._load_table()
            
            PremiumMessage.success(self, MESSAGES.ADMIN.MSG_PURGE_SUCCESS, MESSAGES.ADMIN.TEXT_PURGE_SUCCESS)

            # 5. --- FACTORY RESET ---
            if PremiumMessage.question(self, MESSAGES.ADMIN.TITLE_FACTORY_RESET, MESSAGES.ADMIN.TEXT_FACTORY_RESET):
                db_path = self.sm.db_path
                self.sm.conn.close() 
                
                try:
                    import os
                    if os.path.exists(db_path):
                        os.remove(db_path)
                    import sys
                    sys.exit(0)
                except Exception as ex:
                    PremiumMessage.error(self, MESSAGES.ADMIN.TITLE_SYS_ERROR, MESSAGES.ADMIN.TEXT_SYS_ERROR.format(error=str(ex), path=db_path))

        except Exception as e:
            PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, f"Error durante la purga: {str(e)}")
