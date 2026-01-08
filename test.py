import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime

# ===============================
# LOGIN MOCK
# ===============================
class LoginMock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassGuardian Login (Mock Fase 1)")
        self.setFixedSize(400, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.master_label = QLabel("Clave Maestra:")
        self.master_input = QLineEdit()
        self.master_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Iniciar sesión")
        self.login_btn.clicked.connect(self.handle_login)

        layout.addWidget(self.master_label)
        layout.addWidget(self.master_input)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)

    def handle_login(self):
        # Mock login, cualquier clave sirve
        self.dashboard = DashboardMock()
        self.dashboard.show()
        self.close()

# ===============================
# DASHBOARD MOCK
# ===============================
class DashboardMock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassGuardian Dashboard (Mock Fase 1)")
        self.setMinimumSize(800, 500)

        self.trash = []
        self.data = []  # Lista de registros ficticios

        self.dark_mode = False
        self.init_ui()
        self.start_clock()

    # -------------------------------
    # UI
    # -------------------------------
    def init_ui(self):
        layout = QVBoxLayout()

        # Botones
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Agregar +")
        self.add_btn.clicked.connect(self.add_secret)
        self.trash_btn = QPushButton("Papelera 🗑️")
        self.trash_btn.clicked.connect(self.show_trash)
        self.theme_btn = QPushButton("Modo Dark/Light 🌓")
        self.theme_btn.clicked.connect(self.toggle_theme)

        for b in [self.add_btn, self.trash_btn, self.theme_btn]:
            btn_layout.addWidget(b)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Servicio", "Usuario", "Contraseña", "Fuerza", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Reloj
        self.clock_label = QLabel("")
        self.clock_label.setAlignment(Qt.AlignRight)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.clock_label)
        self.setLayout(layout)

    # -------------------------------
    # RELOJ
    # -------------------------------
    def start_clock(self):
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()

    def update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # -------------------------------
    # ACCIONES MOCK
    # -------------------------------
    def add_secret(self):
        service, ok1 = QInputDialog.getText(self, "Nuevo Servicio", "Nombre del servicio:")
        if not ok1 or not service:
            return

        user, ok2 = QInputDialog.getText(self, "Usuario", "Nombre de usuario:")
        if not ok2 or not user:
            return

        password, ok3 = QInputDialog.getText(self, "Contraseña", "Contraseña (mock):")
        if not ok3 or not password:
            password = "mock1234"

        self.data.append({
            "service": service,
            "user": user,
            "password": password,
            "strength": "Fuerte 🔒"
        })
        self.load_data()

    def load_data(self):
        self.table.setRowCount(len(self.data))
        for row_idx, item in enumerate(self.data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item["service"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item["user"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem("••••••"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item["strength"]))

            # Acciones (solo eliminar)
            action_widget = QWidget()
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_secret(r))
            h_layout.addWidget(delete_btn)
            action_widget.setLayout(h_layout)
            self.table.setCellWidget(row_idx, 4, action_widget)

    def delete_secret(self, row_idx):
        if 0 <= row_idx < len(self.data):
            self.trash.append(self.data[row_idx])
            del self.data[row_idx]
            self.load_data()

    def show_trash(self):
        if not self.trash:
            QMessageBox.information(self, "Papelera", "Papelera vacía")
            return
        trash_text = "\n".join([f"{t['service']} ({t['user']})" for t in self.trash])
        QMessageBox.information(self, "Papelera", trash_text)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0;")
        else:
            self.setStyleSheet("")

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginMock()
    login.show()
    sys.exit(app.exec())


