import secrets
import string
from src.presentation.theme_manager import ThemeManager
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QComboBox, QGraphicsOpacityEffect,
    QSlider, QCheckBox, QFrame, QWidget, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QSettings, QSize
from PyQt5.QtGui import QColor, QFont, QIcon
from src.domain.messages import MESSAGES

class ServiceDialog(QDialog):
    def __init__(self, parent=None, title=None, record=None, secrets_manager=None, app_user="Unknown", user_role="user", settings=None, guardian_ai=None):
        super().__init__(parent)
        self.title_text = title if title else MESSAGES.SERVICE.LBL_SERVICE
        if settings:
            self.settings = settings
        else:
            # [SENIOR FIX] Use User Scope if known
            if app_user and app_user != "Unknown":
                self.settings = QSettings(ThemeManager.APP_ID, f"VultraxCore_{app_user}")
            else:
                self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        self.secrets_manager = secrets_manager
        self.ai = guardian_ai
        self.record = record or {}
        self.app_user = app_user
        self.user_role = user_role
        self.logger = logging.getLogger(__name__)

        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self._force_hide_password)

        self.auto_hide_timer.timeout.connect(self._force_hide_password)

        self.setWindowTitle(self.title_text)
        self.setFixedSize(520, 720)
        
        # Cargar estilos desde el gestor de temas (Respetando el tema del usuario)

        # --- ESTRATEGIA NUCLEAR: WRAPPER FRAME ---
        # En lugar de estilizar el QDialog (que falla en Windows), estilizamos un QFrame interno
        # que ocupa el 100% del espacio.
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.frame = QFrame()
        self.frame.setObjectName("ServiceDialogFrame")
        self.frame.setAttribute(Qt.WA_StyledBackground, True)
        self.main_layout.addWidget(self.frame)
        
        self.theme_manager = ThemeManager()
        user_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme_manager.set_theme(user_theme)
        
        # Aplicar el tema al diálogo usando el gestor
        self.setStyleSheet(self.theme_manager.load_stylesheet("dialogs"))
        
        # Redirigir la construcción del UI al layout del frame
        self._init_ui(self.title_text, parent_widget=self.frame)
        
        if record:
            self.edit_service.setText(record.get("service", ""))
            self.edit_user.setText(record.get("username", app_user))
            self.edit_password.setText(record.get("secret", ""))
            self.edit_notes.setPlainText(record.get("notes", "") or "")
            self._update_strength_meter()
        else:
            self.edit_user.setText(app_user)
        
        self._validate_form()

    def _init_ui(self, title, parent_widget=None):
        target = parent_widget if parent_widget else self
        layout = QVBoxLayout(target)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(18)

        # Header
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("main_title")
        layout.addWidget(title_lbl)

        # SERVICIO
        layout.addWidget(QLabel(MESSAGES.SERVICE.LBL_SERVICE))
        self.edit_service = QLineEdit()
        self.edit_service.setPlaceholderText(MESSAGES.SERVICE.PH_SERVICE)
        self.edit_service.textChanged.connect(self._validate_service_name)
        layout.addWidget(self.edit_service)
        
        self.warning_label = QLabel()
        self.warning_label.setObjectName("danger_text") # Referenciar en QSS o Theme
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        # PROPIETARIO & PRIVACIDAD
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        
    
        v1 = QVBoxLayout()
        l_prop = QLabel(MESSAGES.SERVICE.LBL_OWNER)
        v1.addWidget(l_prop)
        self.edit_user = QLineEdit()
        self.edit_user.setReadOnly(True)
        self.edit_user.setFixedWidth(180)
        self.edit_user.setObjectName("edit_disabled") # Usar un ID para estilo desactivado
        v1.addWidget(self.edit_user)
        row1.addLayout(v1)
        
        v2 = QVBoxLayout()
        v2.addWidget(QLabel(MESSAGES.SERVICE.LBL_PRIVACY))
        self.combo_privacy = QComboBox()
        self.combo_privacy.addItem(MESSAGES.SERVICE.OPT_TEAM, 0)
        self.combo_privacy.addItem(MESSAGES.SERVICE.OPT_PERSONAL, 1)
        if self.record:
            is_priv = self.record.get("is_private", 0)
            idx = self.combo_privacy.findData(is_priv)
            if idx >= 0: self.combo_privacy.setCurrentIndex(idx)
        self._apply_privacy_permissions()
        v2.addWidget(self.combo_privacy)
        row1.addLayout(v2)
        
        layout.addLayout(row1)

        # CONTRASEÑA
        pwd_header = QHBoxLayout()
        pwd_header.addWidget(QLabel(MESSAGES.SERVICE.LBL_PASSWORD))
        pwd_header.addStretch()
        
        self.btn_generate = QPushButton(MESSAGES.SERVICE.BTN_GENERATE)
        self.btn_generate.setObjectName("btn_primary")
        self.btn_generate.setFixedWidth(150)
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.clicked.connect(self._generate_password_advanced)
        pwd_header.addWidget(self.btn_generate)
        layout.addLayout(pwd_header)

        pwd_input_layout = QHBoxLayout()
        pwd_input_layout.setSpacing(8)
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        self.edit_password.setPlaceholderText(MESSAGES.SERVICE.PH_PASSWORD)
        self.edit_password.textChanged.connect(self._update_strength_meter)
        self.edit_password.textChanged.connect(self._validate_form)
        pwd_input_layout.addWidget(self.edit_password)

        self.btn_copy = QPushButton("📋")
        self.btn_copy.setObjectName("btn_secondary")
        self.btn_copy.setFixedSize(36, 36)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        self.btn_copy.setToolTip(MESSAGES.SERVICE.TOOLTIP_COPY)
        pwd_input_layout.addWidget(self.btn_copy)

        self.btn_toggle_pwd = QPushButton(MESSAGES.SERVICE.BTN_SHOW)
        self.btn_toggle_pwd.setObjectName("btn_secondary")
        self.btn_toggle_pwd.setFixedSize(70, 36)
        self.btn_toggle_pwd.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_pwd.clicked.connect(self._toggle_pwd_visibility)
        pwd_input_layout.addWidget(self.btn_toggle_pwd)
        layout.addLayout(pwd_input_layout)

        # STRENGTH
        strength_container = QVBoxLayout()
        strength_container.setSpacing(5)
        
        h_strength = QHBoxLayout()
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        h_strength.addWidget(self.strength_bar)
        
        self.btn_heurist = QPushButton("🛡️")
        self.btn_heurist.setObjectName("btn_secondary")
        self.btn_heurist.setFixedSize(36, 36)
        self.btn_heurist.setCursor(Qt.PointingHandCursor)
        self.btn_heurist.setToolTip(MESSAGES.SERVICE.TOOLTIP_HEURISTIC)
        self.btn_heurist.clicked.connect(self._show_heuristic_analysis)
        h_strength.addWidget(self.btn_heurist)
        strength_container.addLayout(h_strength)

        self.strength_label = QLabel("-")
        self.strength_label.setObjectName("dialog_subtitle")
        strength_container.addWidget(self.strength_label)
        
        layout.addLayout(strength_container)

        # NOTAS
        layout.addWidget(QLabel(MESSAGES.SERVICE.LBL_NOTES))
        self.edit_notes = QTextEdit()
        self.edit_notes.setPlaceholderText(MESSAGES.SERVICE.PH_NOTES)
        self.edit_notes.setFixedHeight(100)
        layout.addWidget(self.edit_notes)

        layout.addStretch()

        # FOOTER
        footer = QHBoxLayout()
        footer.setSpacing(15)
        
        self.btn_cancel = QPushButton(MESSAGES.SERVICE.BTN_CANCEL)
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.clicked.connect(self.reject)
        footer.addWidget(self.btn_cancel, stretch=1)
        
        self.btn_ok = QPushButton(MESSAGES.SERVICE.BTN_SAVE)
        self.btn_ok.setObjectName("btn_primary")
        self.btn_ok.clicked.connect(self.accept)
        
        # Efecto de opacidad para look premium
        self.btn_ok_opacity = QGraphicsOpacityEffect(self.btn_ok)
        self.btn_ok.setGraphicsEffect(self.btn_ok_opacity)
        
        footer.addWidget(self.btn_ok, stretch=2)
        
        layout.addLayout(footer)

    def _toggle_pwd_visibility(self):
        if self.edit_password.echoMode() == QLineEdit.Password:
            self.edit_password.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pwd.setText(MESSAGES.SERVICE.BTN_HIDE)
            self.auto_hide_timer.stop()
            self.auto_hide_timer.start(2500)
        else:
            self._force_hide_password()

    def _force_hide_password(self):
        self.edit_password.setEchoMode(QLineEdit.Password)
        self.btn_toggle_pwd.setText(MESSAGES.SERVICE.BTN_SHOW)
    
    def _validate_service_name(self, text):
        trimmed = text.strip()
        
        if not trimmed or not self.secrets_manager:
            self.warning_label.setVisible(False)
            self._validate_form()
            return
        
        if self.record and self.record.get("service", "").strip().lower() == trimmed.lower():
            self.warning_label.setVisible(False)
        else:
            try:
                if hasattr(self.secrets_manager, 'check_service_exists'):
                    found = self.secrets_manager.check_service_exists(trimmed)
                else:
                    all_s = self.secrets_manager.get_all()
                    found = any(s["service"].strip().lower() == trimmed.lower() for s in all_s)
                
                self.warning_label.setText(MESSAGES.SERVICE.WARN_EXISTS)
                self.warning_label.setVisible(found)
            except Exception as e: 
                self.logger.error(f"Validation error: {e}")
        
        self._validate_form()

    def _validate_form(self):
        service_text = self.edit_service.text().strip()
        pwd_text = self.edit_password.text().strip()
        is_valid = len(service_text) >= 3 and len(pwd_text) > 0 and not self.warning_label.isVisible()
        self.btn_ok.setEnabled(is_valid)
        self.btn_ok_opacity.setOpacity(1.0 if is_valid else 0.4)

    def _generate_password_advanced(self):
        # Usar ajustes de QSettings directamente (Configurados en la página de Ajustes principal)
        length = int(self.settings.value("length", 20))
        use_upper = str(self.settings.value("upper", True)).lower() in ("true", "1")
        use_lower = str(self.settings.value("lower", True)).lower() in ("true", "1")
        use_digits = str(self.settings.value("digits", True)).lower() in ("true", "1")
        use_symbols = str(self.settings.value("symbols", True)).lower() in ("true", "1")
        
        chars = ""
        if use_upper: chars += string.ascii_uppercase
        if use_lower: chars += string.ascii_lowercase
        if use_digits: chars += string.digits
        if use_symbols: chars += "!@#$%^&*()-_=+[]{}<>?/|\\;:.,~"
        if not chars: chars = string.ascii_letters + string.digits

        pwd = "".join(secrets.choice(chars) for _ in range(length))
        self.edit_password.setEchoMode(QLineEdit.Normal)
        self.edit_password.setText(pwd)
        self.btn_toggle_pwd.setText(MESSAGES.SERVICE.BTN_HIDE)
        
        # Auto-hide after 5 seconds
        self.auto_hide_timer.stop()
        self.auto_hide_timer.start(5000)
        self._update_strength_meter()

    def _copy_to_clipboard(self):
        text = self.edit_password.text()
        if text:
            QApplication.clipboard().setText(text)
            self.btn_copy.setText("✅")
            QTimer.singleShot(1500, lambda: self.btn_copy.setText("📋"))

    def _update_strength_meter(self):
        pwd = self.edit_password.text()
        score = 0
        if len(pwd) >= 16: score += 40
        elif len(pwd) >= 12: score += 30
        elif len(pwd) >= 8: score += 15
        
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd): score += 20
        if any(c.isdigit() for c in pwd): score += 20
        if any(c in "!@#$%^&*()-_=+[]{}<>?/|\\;:.,~" for c in pwd): score += 20
        
        score = min(100, score)
        self.strength_bar.setValue(score)
        
        level = "weak"
        if score < 40: level, text = "weak", MESSAGES.SERVICE.STRENGTH_WEAK
        elif score < 75: level, text = "medium", MESSAGES.SERVICE.STRENGTH_MEDIUM
        elif score < 95: level, text = "strong", MESSAGES.SERVICE.STRENGTH_STRONG
        else: level, text = "secure", MESSAGES.SERVICE.STRENGTH_SECURE

        # Aplicar propiedad y forzar refresco
        self.strength_bar.setProperty("strength_level", level)
        self.strength_label.setProperty("strength_level", level)
        self.strength_label.setText(text)
        
        self.strength_bar.style().unpolish(self.strength_bar); self.strength_bar.style().polish(self.strength_bar)
        self.strength_label.style().unpolish(self.strength_label); self.strength_label.style().polish(self.strength_label)

    def _show_heuristic_analysis(self):
        pwd = self.edit_password.text()
        if not pwd:
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.info(self, MESSAGES.SERVICE.HEURISTIC_TITLE, MESSAGES.SERVICE.HEURISTIC_PROMPT)
            return
            
        entropy = self.ai.calculate_entropy(pwd)
        crack_time = self.ai.calculate_crack_time(entropy)
        
        # Análisis de composición
        comp_info = []
        if not any(c.isupper() for c in pwd): comp_info.append(MESSAGES.SERVICE.HEURISTIC_MISSING_UPPER)
        if not any(c.isdigit() for c in pwd): comp_info.append(MESSAGES.SERVICE.HEURISTIC_MISSING_DIGIT)
        if not any(c in "!@#$%^&*()-_=+" for c in pwd): comp_info.append(MESSAGES.SERVICE.HEURISTIC_MISSING_SYMBOL)
        
        findings = "\n".join(comp_info) if comp_info else MESSAGES.SERVICE.HEURISTIC_OPTIMAL
        
        from src.presentation.ui_utils import PremiumMessage
        msg = (f"<b>{MESSAGES.SERVICE.HEURISTIC_REPORT_TITLE}:</b><br><br>"
               f"🌡️ <b>{MESSAGES.SERVICE.HEURISTIC_ENTROPY}:</b> {entropy} bits<br>"
               f"⏱️ <b>{MESSAGES.SERVICE.HEURISTIC_CRACK_TIME}:</b> {crack_time}<br><br>"
               f"💡 <b>{MESSAGES.SERVICE.HEURISTIC_REC}:</b><br>{findings}")
               
        PremiumMessage.info(self, MESSAGES.SERVICE.HEURISTIC_TITLE, msg)

    def _apply_privacy_permissions(self):
        if self.user_role == "admin":
            self.combo_privacy.setEnabled(True)
            return
        
        if not self.record or "owner_name" not in self.record: # Usar owner_name para mas precision
            self.combo_privacy.setEnabled(True)
            return
        
        record_owner = self.record.get("owner_name", "")
        if record_owner.upper() == self.app_user.upper():
            self.combo_privacy.setEnabled(True)
        else:
            self.combo_privacy.setEnabled(False)
            self.combo_privacy.setObjectName("edit_disabled")
    
    def get_data(self):
        return {
            "service": self.edit_service.text().strip(),
            "username": self.edit_user.text().strip(),
            "secret": self.edit_password.text().strip(),
            "notes": self.edit_notes.toPlainText().strip(),
            "is_private": self.combo_privacy.currentData()
        }
