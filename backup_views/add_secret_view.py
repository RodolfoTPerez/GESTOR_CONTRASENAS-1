from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit,
    QPushButton, QVBoxLayout, QMessageBox
)


class AddSecretView(QDialog):
    def __init__(self, secrets_manager, refresh_callback, parent=None):
        super().__init__(parent)
        self.sm = secrets_manager
        self.refresh = refresh_callback

        self.setWindowTitle("Agregar Servicio")
        self.resize(350, 150)
        self.setModal(True)

        form = QFormLayout()
        self.service_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        form.addRow("Servicio:", self.service_edit)
        form.addRow("Usuario:", self.username_edit)
        form.addRow("Contraseña:", self.password_edit)

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save_secret)

        vbox = QVBoxLayout(self)
        vbox.addLayout(form)
        vbox.addWidget(save_btn)

    def save_secret(self):
        service = self.service_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not (service and username and password):
            QMessageBox.warning(self, "Faltan datos", "Complete todos los campos.")
            return

        try:
            self.sm.add_secret(service, username, password)
            QMessageBox.information(self, "Éxito", "Servicio guardado.")
            self.refresh()
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{ex}")
