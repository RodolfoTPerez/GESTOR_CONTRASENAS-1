from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QSettings
from src.presentation.theme_manager import ThemeManager

class TotpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Shield Verification")
        self.setFixedSize(380, 280)
        
        self.theme = ThemeManager()
        self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # Fondo base instantáneo
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))
        
        # Override específico para el input TOTP (Grande y espaciado)
        self.setStyleSheet(self.styleSheet() + f"""
            QLineEdit#totp_input {{
                font-size: 24px; 
                font-weight: 900; 
                letter-spacing: 10px;
                background-color: {colors['bg_sec']};
                color: {colors['primary']};
                border: 2px solid {colors['border']};
            }}
            QLineEdit#totp_input:focus {{ border: 2px solid {colors['primary']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("2FA VERIFICATION")
        title.setObjectName("dialog_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("Ingresa el código de 6 dígitos de tu app.")
        desc.setObjectName("dialog_subtitle")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        self.input = QLineEdit()
        self.input.setObjectName("totp_input")
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setMaxLength(6)
        self.input.setPlaceholderText("000000")
        layout.addWidget(self.input)

        self.btn_verify = QPushButton("VERIFICAR IDENTIDAD")
        self.btn_verify.setObjectName("btn_primary")
        self.btn_verify.setCursor(Qt.PointingHandCursor)
        self.btn_verify.clicked.connect(self.accept)
        layout.addWidget(self.btn_verify)
        
        self.btn_cancel = QPushButton("CANCELAR")
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancel)

    def get_token(self):
        return self.input.text().strip()
