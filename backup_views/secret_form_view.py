from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt
import string
import random

class SecretFormView(QWidget):
    def __init__(self, sm, refresh_callback, secret=None):
        """
        sm: instancia de SecretsManager
        refresh_callback: función para refrescar tabla después de crear/editar
        secret: dict con secret existente para edición, None si es creación
        """
        super().__init__()
        self.sm = sm
        self.refresh_callback = refresh_callback
        self.secret = secret
        self.setWindowTitle("Crear / Editar Servicio")
        self.setGeometry(250, 250, 400, 300)
        self._setup_ui()
        self.show()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Servicio
        self.input_service = QLineEdit()
        self.input_service.setPlaceholderText("Nombre del Servicio")
        if self.secret:
            self.input_service.setText(self.secret["service"])
        self.input_service.textChanged.connect(self.validate_duplicate)

        # Usuario
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuario")
        if self.secret:
            self.input_user.setText(self.secret["user"])

        # Contraseña
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)
        if self.secret:
            self.input_password.setText(self.secret["secret"])
        self.input_password.textChanged.connect(self.update_strength)

        # Barra de fortaleza
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.lbl_strength = QLabel("Fortaleza: ")

        # Botones emoji
        btn_show = QPushButton("👁️")
        btn_show.setCheckable(True)
        btn_show.toggled.connect(self.toggle_password)

        btn_generate = QPushButton("🔐")
        btn_generate.clicked.connect(self.generate_password)

        h_pass_buttons = QHBoxLayout()
        h_pass_buttons.addWidget(btn_show)
        h_pass_buttons.addWidget(btn_generate)

        # Botón Guardar
        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(self.save_secret)

        # Agregar a layout
        layout.addWidget(QLabel("Servicio:"))
        layout.addWidget(self.input_service)
        layout.addWidget(QLabel("Usuario:"))
        layout.addWidget(self.input_user)
        layout.addWidget(QLabel("Contraseña:"))
        layout.addWidget(self.input_password)
        layout.addLayout(h_pass_buttons)
        layout.addWidget(self.pbar)
        layout.addWidget(self.lbl_strength)
        layout.addWidget(btn_save)

        self.setLayout(layout)
        self.validate_duplicate()
        self.update_strength()

    def toggle_password(self, checked):
        if checked:
            self.input_password.setEchoMode(QLineEdit.Normal)
        else:
            self.input_password.setEchoMode(QLineEdit.Password)

    def generate_password(self, length=12):
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        pwd = "".join(random.choice(chars) for _ in range(length))
        self.input_password.setText(pwd)

    def update_strength(self):
        pwd = self.input_password.text()
        score = self.compute_strength_score(pwd)
        self.pbar.setValue(score)
        if score < 40:
            self.lbl_strength.setText("Fortaleza: Débil 🔓")
        elif score < 70:
            self.lbl_strength.setText("Fortaleza: Media")
        else:
            self.lbl_strength.setText("Fortaleza: Fuerte 🔒")

    def compute_strength_score(self, pwd):
        score = 0
        if len(pwd) >= 8:
            score += 30
        if any(c.isupper() for c in pwd):
            score += 20
        if any(c.islower() for c in pwd):
            score += 20
        if any(c.isdigit() for c in pwd):
            score += 15
        if any(c in string.punctuation for c in pwd):
            score += 15
        return min(score, 100)

    def validate_duplicate(self):
        service = self.input_service.text().strip().lower()
        user = self.input_user.text().strip().lower()
        secrets = self.sm.get_all()
        duplicate = any(
            s["service"].lower() == service and s["user"].lower() == user
            and (not self.secret or s["id"] != self.secret["id"])
            for s in secrets
        )
        if duplicate:
            self.input_service.setStyleSheet("border: 2px solid red;")
        else:
            self.input_service.setStyleSheet("")

    def save_secret(self):
        service = self.input_service.text().strip()
        user = self.input_user.text().strip()
        password = self.input_password.text().strip()
        if not service or not user or not password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return
        # Validación duplicado
        self.validate_duplicate()
        if "red" in self.input_service.styleSheet():
            QMessageBox.warning(self, "Error", "Este servicio ya existe para este usuario")
            return
        if self.secret:
            self.sm.update_secret(self.secret["id"], service, user, password)
        else:
            self.sm.create_secret(service, user, password)
        self.refresh_callback()
        self.close()
