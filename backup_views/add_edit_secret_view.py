from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QProgressBar
)
from src.infrastructure.secrets_manager import SecretsManager
import random, string

class AddEditSecretView(QDialog):
    def __init__(self, sm: SecretsManager, secret_data=None):
        super().__init__()
        self.setWindowTitle("Agregar / Editar Secreto")
        self.resize(400, 300)
        self.sm = sm
        self.secret_data = secret_data

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Campos
        self.service_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel("Servicio:"))
        layout.addWidget(self.service_input)
        layout.addWidget(QLabel("Usuario:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Contraseña:"))
        layout.addWidget(self.password_input)

        # Barra de fortaleza
        self.strength_bar = QProgressBar()
        layout.addWidget(self.strength_bar)

        # Botones
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("🔐 Generar fuerte")
        self.show_btn = QPushButton("👁️ Mostrar/Ocultar")
        self.save_btn = QPushButton("💾 Guardar")
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.show_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        # Conectar señales
        self.generate_btn.clicked.connect(self.generate_password)
        self.show_btn.clicked.connect(self.toggle_password)
        self.save_btn.clicked.connect(self.save_secret)
        self.password_input.textChanged.connect(self.update_strength)

        # Si estamos editando, rellenar campos
        if secret_data:
            self.service_input.setText(secret_data['service'])
            self.username_input.setText(secret_data['username'])
            self.password_input.setText(secret_data['password'])

        # Validación inmediata del servicio
        self.service_input.textChanged.connect(self.check_duplicate_service)

    def generate_password(self):
        pwd = ''.join(random.choices(
            string.ascii_letters + string.digits + "!@#$%^&*()",
            k=16
        ))
        self.password_input.setText(pwd)

    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def update_strength(self):
        pwd = self.password_input.text()
        score = self.check_strength(pwd)
        self.strength_bar.setValue(score)
        self.strength_bar.setFormat(f"{score}% {'Fuerte' if score>=70 else 'Débil'}")

    def check_strength(self, password: str) -> int:
        score = min(len(password) * 10, 50)
        if any(c.isupper() for c in password):
            score += 10
        if any(c.islower() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in "!@#$%^&*()" for c in password):
            score += 10
        return min(score, 100)

    def check_duplicate_service(self):
        service = self.service_input.text()
        all_secrets = self.sm.get_all(include_deleted=True)
        for s in all_secrets:
            if s[1].lower() == service.lower():
                self.service_input.setStyleSheet("border: 2px solid red;")
                return
        self.service_input.setStyleSheet("")

    def save_secret(self):
        service = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not service or not username or not password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        # Validar duplicado
        all_secrets = self.sm.get_all(include_deleted=True)
        for s in all_secrets:
            if s[1].lower() == service.lower() and (not self.secret_data or s[0] != self.secret_data['id']):
                QMessageBox.warning(self, "Error", "El servicio ya existe")
                return

        if self.secret_data:
            # Editar
            # TODO: implementar edición en SecretsManager
            QMessageBox.information(self, "Editar", "Funcionalidad de edición aún por implementar")
        else:
            # Crear
            self.sm.add_secret(service, username, password)
            QMessageBox.information(self, "Éxito", "Secreto agregado correctamente")
            self.accept()
