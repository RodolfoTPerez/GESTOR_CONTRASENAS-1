from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QStackedWidget, QWidget, QFrame, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
import os
import uuid
import logging
from src.domain.messages import MESSAGES

from src.presentation.theme_manager import ThemeManager

class SetupWizard(QDialog):
    def __init__(self, secrets_manager, user_manager, parent=None):
        super().__init__(parent)
        self.sm = secrets_manager
        self.um = user_manager
        self.logger = logging.getLogger(__name__)
        self.theme = ThemeManager()
        
        self.setWindowTitle(MESSAGES.WIZARD.TITLE)
        self.setFixedSize(650, 450)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setup_result = {
            "lang": "ES",
            "instance_name": "",
            "admin_user": "",
            "admin_pass": ""
        }

        self._init_ui()

    def _init_ui(self):
        # Contenedor con bordes redondeados y estilo dinámico
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setGeometry(0, 0, 650, 450)
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))
        
        # Estilo específico para el MainFrame redondeado que no está en el QSS global o requiere override
        colors = self.theme.get_theme_colors()
        self.main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {colors['bg']};
                border: 2px solid {colors['primary']}66;
                border-radius: 20px;
            }}
        """)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header
        self.lbl_title = QLabel(MESSAGES.WIZARD.TITLE)
        self.lbl_title.setObjectName("dialog_subtitle")
        layout.addWidget(self.lbl_title)

        # Stack de Pasos
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_step1())
        self.stack.addWidget(self._create_step2())
        self.stack.addWidget(self._create_step3())
        self.stack.addWidget(self._create_step4())
        layout.addWidget(self.stack)

        # Footer (Botones Navegación)
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton(MESSAGES.WIZARD.BTN_BACK)
        self.btn_back.setObjectName("btn_secondary")
        self.btn_back.hide()
        self.btn_back.clicked.connect(self._go_back)
        
        self.btn_next = QPushButton(MESSAGES.WIZARD.BTN_NEXT)
        self.btn_next.setObjectName("btn_primary")
        self.btn_next.clicked.connect(self._go_next)
        
        nav_layout.addWidget(self.btn_back)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        layout.addLayout(nav_layout)

    def _create_step1(self):
        page = QWidget()
        v = QVBoxLayout(page)
        h = QLabel(MESSAGES.WIZARD.STEP1_HEAD)
        h.setObjectName("main_title")
        d = QLabel(MESSAGES.WIZARD.STEP1_DESC)
        d.setObjectName("dialog_subtitle")
        d.setWordWrap(True)
        v.addWidget(h); v.addWidget(d); v.addSpacing(20)

        self.btn_lang_es = QRadioButton("Español (ES)")
        self.btn_lang_en = QRadioButton("English (EN)")
        self.btn_lang_es.setChecked(True)
        
        colors = self.theme.get_theme_colors()
        radio_style = f"font-size: 16px; padding: 10px; color: {colors['text']};"
        self.btn_lang_es.setStyleSheet(radio_style)
        self.btn_lang_en.setStyleSheet(radio_style)
        
        v.addWidget(self.btn_lang_es)
        v.addWidget(self.btn_lang_en); v.addStretch()
        return page

    def _create_step2(self):
        page = QWidget()
        v = QVBoxLayout(page)
        h = QLabel(MESSAGES.WIZARD.STEP2_HEAD)
        h.setObjectName("main_title")
        d = QLabel(MESSAGES.WIZARD.STEP2_DESC)
        d.setObjectName("dialog_subtitle")
        v.addWidget(h); v.addWidget(d); v.addSpacing(20)

        self.input_instance = QLineEdit()
        self.input_instance.setPlaceholderText(MESSAGES.WIZARD.STEP2_PLACEHOLDER)
        v.addWidget(self.input_instance); v.addStretch()
        return page

    def _create_step3(self):
        page = QWidget()
        v = QVBoxLayout(page)
        h = QLabel(MESSAGES.WIZARD.STEP3_HEAD)
        h.setObjectName("main_title")
        v.addWidget(h); v.addSpacing(15)

        lbl_admin = QLabel(MESSAGES.WIZARD.LBL_ADMIN_USER)
        lbl_admin.setObjectName("dialog_subtitle")
        v.addWidget(lbl_admin)
        self.input_user = QLineEdit()
        v.addWidget(self.input_user)

        lbl_pass = QLabel(MESSAGES.WIZARD.LBL_MASTER_PWD)
        lbl_pass.setObjectName("dialog_subtitle")
        v.addWidget(lbl_pass)
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.Password)
        v.addWidget(self.input_pass); v.addStretch()
        return page

    def _create_step4(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setAlignment(Qt.AlignCenter)
        h = QLabel("✨ " + MESSAGES.WIZARD.STEP4_HEAD)
        h.setObjectName("main_title")
        h.setStyleSheet("font-size: 36px;") # Mantener tamaño extra
        d = QLabel(MESSAGES.WIZARD.STEP4_DESC)
        d.setObjectName("dialog_subtitle")
        v.addWidget(h); v.addWidget(d)
        return page

    def _go_next(self):
        idx = self.stack.currentIndex()
        if idx == 0: # Idioma
            MESSAGES.LANG = "ES" if self.btn_lang_es.isChecked() else "EN"
            self._update_all_labels()
            self.btn_back.show()
        elif idx == 1: # Nombre
            if not self.input_instance.text().strip(): return
        elif idx == 2: # Pass
            if not self.input_user.text().strip() or not self.input_pass.text(): return

        if idx < 3:
            self.stack.setCurrentIndex(idx + 1)
            if idx + 1 == 3:
                self.btn_next.setText(MESSAGES.WIZARD.BTN_FINISH)
        else:
            self._finalize()

    def _go_back(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self.btn_next.setText(MESSAGES.WIZARD.BTN_NEXT)
            if idx - 1 == 0: self.btn_back.hide()

    def _update_all_labels(self):
        # Actualización dinámica si cambia el idioma en el primer paso
        self.btn_next.setText(MESSAGES.WIZARD.BTN_NEXT)
        self.btn_back.setText(MESSAGES.WIZARD.BTN_BACK)

    def _finalize(self):
        # 1. Preparar datos
        instance_name = self.input_instance.text().strip() or "VULTRAX CORE"
        admin_user = self.input_user.text().strip()
        admin_pass = self.input_pass.text()
        
        self.logger.info(f"Starting wizard configuration for instance: {instance_name}")

        import uuid
        v_id = str(uuid.uuid4())
        try:
            # Esta es la tabla que manda en el esquema de UUIDs
            self.um.supabase.table("vaults").upsert({
                "id": v_id, 
                "name": instance_name
            }).execute()
            self.logger.info(f"Master Vault configured with UUID {v_id}")
            
            # Intento opcional en vault_groups por si acaso
            try: self.um.supabase.table("vault_groups").upsert({"id": 1, "vault_name": instance_name, "vault_master_key": os.urandom(32).hex()}).execute()
            except: pass
        except Exception as e:
            self.logger.error(f"Wizard Error: {e}")
            # Error handling for vault creation
            PremiumMessage.error(self, MESSAGES.WIZARD.TITLE_ERROR, MESSAGES.WIZARD.MSG_ERROR_VAULT.format(e=e))
            return

        # 3. ASIGNAR CONTEXTO A LA SESIÓN
        self.sm.current_vault_id = v_id
        self.sm.set_meta("instance_name", instance_name)
        self.sm.set_meta("language", MESSAGES.LANG)

        # 4. CREAR AL ADMINISTRADOR (Sincronización profesional de llaves)
        success, msg = self.um.add_new_user(admin_user, "admin", admin_pass)
        
        if success:
            self.logger.info(f"Wizard Configuration Successful for {instance_name}")
            self.accept()
        else:
            # Error handling for profile creation
            # from PyQt5.QtWidgets import QMessageBox # Clean up import if visible
            PremiumMessage.error(self, MESSAGES.WIZARD.TITLE_ERROR, MESSAGES.WIZARD.MSG_ERROR_PROFILE.format(msg=msg))
