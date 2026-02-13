from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, 
    QLineEdit, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QSettings
from src.presentation.theme_manager import ThemeManager
from src.presentation.ui_utils import PremiumMessage
from src.domain.messages import MESSAGES

class VaultRepairDialog(QDialog):
    def __init__(self, username, secrets_manager, parent=None):
        super().__init__(parent)
        self.username = username
        self.sm = secrets_manager
        self.theme = ThemeManager()
        self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        
        # Sincronizar tema ANTES para evitar destellos blancos
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # Fondo base instantáneo
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        
        self.setWindowTitle(MESSAGES.RECOVERY.REPAIR_TITLE)
        self.setFixedSize(400, 480)
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Icono Header
        icon = QLabel("🔐")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 40px;")
        layout.addWidget(icon)

        title = QLabel(MESSAGES.RECOVERY.REPAIR_HEADER)
        title.setObjectName("dialog_title")
        title.setStyleSheet(f"color: {colors['danger']};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel(
            MESSAGES.RECOVERY.REPAIR_DESC.format(username=self.username)
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setObjectName("dialog_subtitle")
        layout.addWidget(desc)

        # Inputs
        # Inputs
        layout.addWidget(QLabel(MESSAGES.RECOVERY.LBL_OLD_PWD))
        self.input_old = QLineEdit()
        self.input_old.setEchoMode(QLineEdit.Password)
        self.input_old.setPlaceholderText(MESSAGES.RECOVERY.PH_OLD_PWD)
        layout.addWidget(self.input_old)
        
        layout.addWidget(QLabel(MESSAGES.RECOVERY.LBL_NEW_PWD))
        self.input_current = QLineEdit()
        self.input_current.setEchoMode(QLineEdit.Password)
        self.input_current.setPlaceholderText(MESSAGES.RECOVERY.PH_NEW_PWD)
        layout.addWidget(self.input_current)

        layout.addStretch()

        # Botones
        # Botones
        self.btn_repair = QPushButton(MESSAGES.RECOVERY.BTN_REPAIR)
        self.btn_repair.setObjectName("btn_danger")
        self.btn_repair.clicked.connect(self.attempt_repair)
        layout.addWidget(self.btn_repair)
        
        btn_cancel = QPushButton(MESSAGES.RECOVERY.BTN_CANCEL)
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    def attempt_repair(self):
        old_pass = self.input_old.text().strip()
        new_pass = self.input_current.text().strip()
        
        if not old_pass or not new_pass:
            PremiumMessage.warning(self, MESSAGES.COMMON.TITLE_INFO, MESSAGES.RECOVERY.MSG_INCOMPLETE)
            return
            
        self.btn_repair.setText(MESSAGES.RECOVERY.BTN_PROCESSING)
        self.btn_repair.setEnabled(False)
        self.repaint()
        
        # Intentar reparación
        success, msg = self.sm.repair_vault_access(self.username, old_pass, new_pass)
        
        self.btn_repair.setEnabled(True)
        self.btn_repair.setText(MESSAGES.RECOVERY.BTN_REPAIR)
        
        if success:
            PremiumMessage.information(self, MESSAGES.RECOVERY.MSG_SUCCESS_TITLE, MESSAGES.RECOVERY.MSG_SUCCESS_TEXT)
            self.accept()
        else:
            PremiumMessage.critical(self, MESSAGES.RECOVERY.MSG_FAIL_TITLE, 
                MESSAGES.RECOVERY.MSG_FAIL_TEXT.format(msg=msg))

class OrphanRescueDialog(QDialog):
    def __init__(self, admin_username, user_manager, parent=None):
        super().__init__(parent)
        self.admin_username = admin_username
        self.user_manager = user_manager
        self.theme = ThemeManager()
        self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        
        self.setWindowTitle(MESSAGES.RECOVERY.ORPHAN_TITLE)
        self.setFixedSize(450, 300)
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30,30,30,30)
        
        layout.addWidget(QLabel(f"<h2>{MESSAGES.RECOVERY.ORPHAN_HEADER}</h2>"))
        
        msg = QLabel(MESSAGES.RECOVERY.ORPHAN_DESC)
        msg.setWordWrap(True)
        layout.addWidget(msg)
        
        layout.addStretch()
        
        self.btn_run = QPushButton(MESSAGES.RECOVERY.BTN_RUN)
        self.btn_run.setObjectName("btn_primary")
        self.btn_run.clicked.connect(self.run_rescue)
        layout.addWidget(self.btn_run)
        
        self.btn_forensic = QPushButton(MESSAGES.RECOVERY.BTN_FORENSIC)
        self.btn_forensic.setObjectName("btn_primary") 
        self.btn_forensic.clicked.connect(self.run_forensic)
        layout.addWidget(self.btn_forensic)

    def run_rescue(self):
        self.btn_run.setText(MESSAGES.RECOVERY.BTN_RUNNING)
        self.btn_run.setEnabled(False)
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        success, msg = self.user_manager.repair_orphans(self.admin_username)
        
        self.btn_run.setEnabled(True)
        self.btn_run.setText(MESSAGES.RECOVERY.BTN_FINISHED)
        
        if success:
            PremiumMessage.information(self, MESSAGES.RECOVERY.MSG_RESULT, f"✅ {msg}" + MESSAGES.RECOVERY.MSG_RESULT_HINT)
        else:
            PremiumMessage.warning(self, MESSAGES.RECOVERY.MSG_RESULT, f"⚠️ {MESSAGES.RECOVERY.MSG_REPORT}:\n{msg}")

    def run_forensic(self):
        self.btn_forensic.setText(MESSAGES.RECOVERY.BTN_ANALYZING)
        self.btn_forensic.setEnabled(False)
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Necesitamos el SecretsManager, que debería estar en user_manager.sm
        if self.user_manager.sm:
            count, msg = self.user_manager.sm.attempt_legacy_recovery()
            PremiumMessage.information(self, MESSAGES.RECOVERY.MSG_REPORT, msg)
        else:
            PremiumMessage.critical(self, MESSAGES.COMMON.TITLE_ERROR, MESSAGES.RECOVERY.MSG_ERROR_SM)
            
        self.btn_forensic.setEnabled(True)
        self.btn_forensic.setText(MESSAGES.RECOVERY.BTN_FORENSIC)
            
class AccountRecoveryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(MESSAGES.RECOVERY.ACCOUNT_TITLE)
        self.setFixedSize(400, 300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(MESSAGES.RECOVERY.ACCOUNT_DESC))
        btn = QPushButton(MESSAGES.RECOVERY.BTN_UNDERSTOOD)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
