from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from src.infrastructure.secrets_manager import SecretsManager, password_strength
import secrets, string

class SecretsView(QWidget):
    def __init__(self, master_password: str):
        super().__init__()
        self.setWindowTitle("PassGuardian - Gestión de Credenciales")
        self.resize(950, 650)

        # ===========================
        # Modelo / Infraestructura
        # ===========================
        self.manager = SecretsManager(master_password)

        # ===========================
        # Componentes UI
        # ===========================
        self.service_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.complexity_label = QLabel("Seguridad: ")
        self.complexity_percent = QLabel("0%")

        self.generate_btn = QPushButton("🔐 Generar contraseña fuerte")
        self.show_btn = QPushButton("👁️ Ver / Ocultar contraseña")
        self.add_btn = QPushButton("Agregar / Actualizar")
        self.restore_btn = QPushButton("♻️ Restaurar desde papelera")

        # Tabla de secretos
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Servicio", "Usuario", "Seguridad", "Estado", "Editar", "Eliminar", "Restaurar"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Layout
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Servicio"))
        form_layout.addWidget(self.service_input)
        form_layout.addWidget(QLabel("Usuario"))
        form_layout.addWidget(self.user_input)
        form_layout.addWidget(QLabel("Contraseña"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.complexity_label)
        form_layout.addWidget(self.complexity_percent)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.show_btn)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.restore_btn)
        form_layout.addLayout(btn_layout)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

        # ===========================
        # Conexiones
        # ===========================
        self.password_input.textChanged.connect(self.update_complexity)
        self.generate_btn.clicked.connect(self.generate_password)
        self.show_btn.clicked.connect(self.toggle_password)
        self.add_btn.clicked.connect(self.add_or_update_secret)
        self.restore_btn.clicked.connect(self.restore_from_trash)
        self.table.cellClicked.connect(self.table_action)

        self.show_password = False
        self.load_table()

    # ===========================
    # Funciones UI
    # ===========================
    def update_complexity(self):
        pwd = self.password_input.text()
        percent, level = password_strength(pwd)
        self.complexity_label.setText(f"Seguridad: {level}")
        self.complexity_percent.setText(f"{percent}%")

    def generate_password(self):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?/`~"
        pwd = ''.join(secrets.choice(alphabet) for _ in range(16))
        self.password_input.setText(pwd)

    def toggle_password(self):
        self.show_password = not self.show_password
        self.password_input.setEchoMode(QLineEdit.Normal if self.show_password else QLineEdit.Password)

    def add_or_update_secret(self):
        service = self.service_input.text().strip()
        user = self.user_input.text().strip()
        pwd = self.password_input.text()

        if not service or not user or not pwd:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        if self.manager.exists_service(service):
            self.manager.update_secret(service, pwd)
            QMessageBox.information(self, "Actualizado", f"Se actualizó el servicio '{service}'")
        else:
            self.manager.add_secret(service, user, pwd)
            QMessageBox.information(self, "Agregado", f"Se agregó el servicio '{service}'")
        self.load_table()
        self.clear_form()

    def clear_form(self):
        self.service_input.clear()
        self.user_input.clear()
        self.password_input.clear()
        self.complexity_label.setText("Seguridad: ")
        self.complexity_percent.setText("0%")

    def load_table(self):
        secrets_list = self.manager.list_secrets(include_deleted=True)
        self.table.setRowCount(len(secrets_list))
        for row_idx, secret in enumerate(secrets_list):
            pwd = self.manager.get_secret(secret["service"])
            percent, level = password_strength(pwd) if pwd else (0, "Eliminado")
            icon = "🔒" if level == "Fuerte" else "🔓" if level != "Eliminado" else "🗑️"

            self.table.setItem(row_idx, 0, QTableWidgetItem(secret["service"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(secret["user"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{percent}% {level}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(icon))
            self.table.setItem(row_idx, 4, QTableWidgetItem("Editar"))
            self.table.setItem(row_idx, 5, QTableWidgetItem("Eliminar"))
            self.table.setItem(row_idx, 6, QTableWidgetItem("Restaurar"))

    def table_action(self, row, column):
        service = self.table.item(row, 0).text()
        if column == 4:  # Editar
            secret_data = self.manager.get_secret(service)
            if secret_data:
                self.service_input.setText(service)
                self.user_input.setText(self.table.item(row, 1).text())
                self.password_input.setText(secret_data)
                self.update_complexity()
        elif column == 5:  # Eliminar
            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Desea eliminar el servicio '{service}'?",
            )
            if confirm == QMessageBox.Yes:
                self.manager.delete_secret(service)
                self.load_table()
        elif column == 6:  # Restaurar
            if self.manager.is_deleted(service):
                self.manager.restore_secret(service)
                self.load_table()

    def restore_from_trash(self):
        selected_rows = set(idx.row() for idx in self.table.selectedIndexes())
        for row in selected_rows:
            service = self.table.item(row, 0).text()
            if self.manager.is_deleted(service):
                self.manager.restore_secret(service)
        self.load_table()


