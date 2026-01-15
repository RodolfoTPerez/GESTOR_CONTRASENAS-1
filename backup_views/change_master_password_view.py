from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class ChangeMasterPasswordView(QDialog):
    def __init__(self, secrets_manager, totp_secret, parent=None):
        super().__init__(parent)

        self.sm = secrets_manager
        self.totp_secret = totp_secret

        self.setWindowTitle("Cambiar Contraseña Maestra")
        self.setModal(True)
        self.resize(400, 250)

        layout = QVBoxLayout()

        # Contraseña actual
        self.old_pass_label = QLabel("Contraseña actual:")
        self.old_pass_input = QLineEdit()
        self.old_pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.old_pass_label)
        layout.addWidget(self.old_pass_input)

        # Nueva contraseña
        self.new_pass_label = QLabel("Nueva contraseña:")
        self.new_pass_input = QLineEdit()
        self.new_pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_pass_label)
        layout.addWidget(self.new_pass_input)

        # Confirmación
        self.confirm_label = QLabel("Confirmar nueva contraseña:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_label)
        layout.addWidget(self.confirm_input)

        # Botón
        self.save_btn = QPushButton("Guardar")
        self.save_btn.clicked.connect(self.change_password)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    # ---------------------------------------------------------
    # LÓGICA PARA CAMBIAR CONTRASEÑA MAESTRA
    # ---------------------------------------------------------
    def change_password(self):
        old_pass = self.old_pass_input.text().strip()
        new_pass = self.new_pass_input.text().strip()
        confirm = self.confirm_input.text().strip()

        if not old_pass or not new_pass or not confirm:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        if new_pass != confirm:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            return

        try:
            # Validar contraseña actual
            self.sm.verify_master_password(old_pass)

            # Cambiar contraseña
            self.sm.change_master_password(old_pass, new_pass, self.totp_secret)

            QMessageBox.information(self, "Éxito", "Contraseña cambiada correctamente.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
