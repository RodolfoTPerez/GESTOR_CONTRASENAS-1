# C:\PassGuardian\src\presentation\dashboard_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem
from .add_secret_view import AddSecretView

class DashboardView(QWidget):
    def __init__(self, secrets_manager):
        super().__init__()
        self.sm = secrets_manager
        self.setWindowTitle("PassGuardian Dashboard")
        layout = QVBoxLayout()
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.add_btn = QPushButton("Agregar Servicio")
        self.add_btn.clicked.connect(self.add_secret)
        layout.addWidget(self.add_btn)
        self.setLayout(layout)
        self.refresh_table()

    def refresh_table(self):
        secrets = self.sm.get_all()
        self.table.setRowCount(len(secrets))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Servicio", "Usuario", "Contraseña"])
        for row, secret in enumerate(secrets):
            self.table.setItem(row, 0, QTableWidgetItem(secret["service"]))
            self.table.setItem(row, 1, QTableWidgetItem(secret["username"]))
            self.table.setItem(row, 2, QTableWidgetItem("●●●●●●"))

    def add_secret(self):
        add_window = AddSecretView(self.sm, self.refresh_table)
        add_window.show()
