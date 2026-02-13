from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from src.presentation.ui_utils import PremiumMessage
from PyQt5.QtCore import Qt

class AISettingsDialog(QDialog):
    def __init__(self, current_engine, current_key, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de IA")
        self.setFixedSize(400, 220)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)

        # Motor IA
        engine_layout = QHBoxLayout()
        engine_label = QLabel("Motor IA:")
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Gemini", "ChatGPT"])
        if current_engine:
            idx = self.engine_combo.findText(current_engine, Qt.MatchFixedString)
            if idx >= 0:
                self.engine_combo.setCurrentIndex(idx)
        engine_layout.addWidget(engine_label)
        engine_layout.addWidget(self.engine_combo)
        layout.addLayout(engine_layout)

        # API Key
        key_layout = QHBoxLayout()
        key_label = QLabel("API Key:")
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setText(current_key or "")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Guardar")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def get_settings(self):
        return {
            "engine": self.engine_combo.currentText(),
            "api_key": self.key_edit.text().strip()
        }
