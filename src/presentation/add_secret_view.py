from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QProgressBar
from PySide6.QtCore import Qt
#from infrastructure.secrets_manager import SecretsManager
from src.infrastructure.secrets_manager import SecretsManager
import re

class AddSecretView(QWidget):
    def __init__(self, secrets_manager: SecretsManager, refresh_callback):
        super().__init__()
        self.setWindowTitle("Agregar Nuevo Servicio")
        self.sm = secrets_manager
        self.refresh_callback = refresh_callback

        layout = QVBoxLayout()

        # Service
        layout.addWidget(QLabel("Service:"))
        self.service_input = QLineEdit()
        layout.addWidget(self.service_input)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.update_strength)
        layout.addWidget(self.password_input)

        # Mostrar contraseña
        self.show_password_btn = QPushButton("👁️ Mostrar / Ocultar")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.toggled.connect(self.toggle_password)
        layout.addWidget(self.show_password_btn)

        # Barra de fuerza
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        layout.addWidget(self.strength_bar)
        self.strength_label = QLabel("Seguridad de contraseña: ")
        layout.addWidget(self.strength_label)

        # Botones
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Agregar 🔐")
        self.add_btn.clicked.connect(self.add_secret)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_password(self, checked):
        self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def password_strength(self, pwd):
        score = 0
        length = len(pwd)
        score += min(20, length * 5)  # hasta 20 puntos por longitud
        if re.search(r"[a-z]", pwd):
            score += 20
        if re.search(r"[A-Z]", pwd):
            score += 20
        if re.search(r"[0-9]", pwd):
            score += 20
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
            score += 20
        return min(score, 100)

    def update_strength(self):
        pwd = self.password_input.text()
        strength = self.password_strength(pwd)
        self.strength_bar.setValue(strength)
        emoji = "🔒" if strength >= 80 else "🔓"
        self.strength_label.setText(f"Seguridad de contraseña: {strength}% {emoji}")

    def add_secret(self):
        service = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Validación campos vacíos
        if not service or not username or not password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        # Validación duplicados
        existing = self.sm.get_all(include_deleted=True)
        for s in existing:
            if s["service"].lower() == service.lower() and s["username"].lower() == username.lower():
                QMessageBox.warning(self, "Error", "Ya existe este servicio con este username")
                return

        # Validación fuerza
        if self.password_strength(password) < 50:
            QMessageBox.warning(self, "Error", "Contraseña demasiado débil")
            return

        self.sm.add_secret(service, username, password)
        self.refresh_callback()
        QMessageBox.information(self, "Éxito", "Servicio agregado correctamente 🔐")
        self.close()



