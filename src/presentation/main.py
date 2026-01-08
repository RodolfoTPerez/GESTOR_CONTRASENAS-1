import sys
import os
import secrets
import string
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QProgressBar, QListWidget,
    QMessageBox, QMenu, QAction
)
from PySide6.QtCore import Qt
from cryptography.hazmat.primitives.kdf.argon2 import Argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ----------------------------
# Configuración
# ----------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "passguardian_encrypted.db")
MASTER_KEY = b'masterpasswordmustbereplaced'  # Temporal: derivar de clave maestra real

# ----------------------------
# Funciones de seguridad
# ----------------------------
def derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = Argon2(length=32, salt=salt, parallelism=2, memory_cost=102400, iterations=2)
    return kdf.derive(master_password.encode())

def encrypt_password(password: str, key: bytes):
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aesgcm.encrypt(nonce, password.encode(), None)
    return ct, nonce

def decrypt_password(ct: bytes, key: bytes, nonce: bytes) -> str:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()

# ----------------------------
# Base de datos
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT UNIQUE,
            username TEXT,
            password BLOB,
            nonce BLOB,
            created_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# ----------------------------
# Funciones de contraseña
# ----------------------------
def generate_strong_password(length=16) -> str:
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

def password_strength(password: str) -> int:
    score = 0
    length = len(password)
    if length >= 8: score += 25
    if any(c.islower() for c in password): score += 15
    if any(c.isupper() for c in password): score += 20
    if any(c.isdigit() for c in password): score += 20
    if any(c in string.punctuation for c in password): score += 20
    return min(score, 100)

# ----------------------------
# UI / Main Window
# ----------------------------
class PassGuardian(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassGuardian - LOCKED v1.0")
        self.setGeometry(100, 100, 900, 600)
        self.key = derive_key("masterpassword", b'somesaltvalue12')  # Temporal
        init_db()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Inputs
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("Servicio")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Botones de contraseña
        self.btn_generate = QPushButton("🔐 Generar contraseña")
        self.btn_generate.clicked.connect(self.generate_password)
        self.btn_show = QPushButton("👁️")
        self.btn_show.setCheckable(True)
        self.btn_show.toggled.connect(self.toggle_password)

        # Barra de complejidad
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        self.strength_label = QLabel("Seguridad: N/A")

        # Botón guardar
        self.btn_save = QPushButton("Guardar registro")
        self.btn_save.clicked.connect(self.save_secret)

        # Dashboard
        self.dashboard_label = QLabel("Dashboard: N/A")

        # Lista de registros con menú contextual
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        # Layouts
        layout.addWidget(self.service_input)
        layout.addWidget(self.username_input)
        pw_layout = QHBoxLayout()
        pw_layout.addWidget(self.password_input)
        pw_layout.addWidget(self.btn_show)
        pw_layout.addWidget(self.btn_generate)
        layout.addLayout(pw_layout)
        layout.addWidget(self.pbar)
        layout.addWidget(self.strength_label)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.dashboard_label)
        layout.addWidget(QLabel("Registros:"))
        layout.addWidget(self.list_widget)

        self.setLayout(layout)
        self.password_input.textChanged.connect(self.update_strength)
        self.load_secrets()
        self.update_dashboard()

    # ----------------------------
    # Funcionalidades UI
    # ----------------------------
    def update_strength(self):
        pwd = self.password_input.text()
        score = password_strength(pwd)
        self.pbar.setValue(score)
        if score < 50:
            self.strength_label.setText("Seguridad: Débil 🔓")
        elif score < 80:
            self.strength_label.setText("Seguridad: Media ⚠️")
        else:
            self.strength_label.setText("Seguridad: Fuerte 🔒")

    def generate_password(self):
        pwd = generate_strong_password()
        self.password_input.setText(pwd)

    def toggle_password(self, checked):
        self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    # ----------------------------
    # Gestión de secretos
    # ----------------------------
    def save_secret(self):
        service = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not service or not username or not password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM secrets WHERE service=? AND deleted=0", (service,))
        if c.fetchone():
            QMessageBox.warning(self, "Error", "Servicio ya existe")
            conn.close()
            return

        ct, nonce = encrypt_password(password, self.key)
        created_at = datetime.utcnow().isoformat()
        c.execute(
            "INSERT INTO secrets (service, username, password, nonce, created_at) VALUES (?,?,?,?,?)",
            (service, username, ct, nonce, created_at)
        )
        conn.commit()
        conn.close()
        self.clear_inputs()
        self.load_secrets()
        self.update_dashboard()

    def load_secrets(self):
        self.list_widget.clear()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT service, username FROM secrets WHERE deleted=0")
        rows = c.fetchall()
        for row in rows:
            self.list_widget.addItem(f"{row[0]} ({row[1]})")
        conn.close()

    # ----------------------------
    # Context menu acciones
    # ----------------------------
    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        menu.addAction("Editar", lambda: self.edit_secret(item))
        menu.addAction("Eliminar", lambda: self.delete_secret(item))
        menu.addAction("Restaurar", lambda: self.restore_secret(item))
        menu.addAction("Ver contraseña", lambda: self.view_secret(item))
        menu.addAction("Copiar contraseña", lambda: self.copy_secret(item))
        menu.exec(self.list_widget.mapToGlobal(pos))

    # ----------------------------
    # Operaciones CRUD
    # ----------------------------
    def delete_secret(self, item):
        service = item.text().split(" ")[0]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE secrets SET deleted=1 WHERE service=?", (service,))
        conn.commit()
        conn.close()
        self.load_secrets()
        self.update_dashboard()

    def restore_secret(self, item):
        service = item.text().split(" ")[0]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE secrets SET deleted=0 WHERE service=?", (service,))
        conn.commit()
        conn.close()
        self.load_secrets()
        self.update_dashboard()

    def view_secret(self, item):
        service = item.text().split(" ")[0]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password, nonce FROM secrets WHERE service=? AND deleted=0", (service,))
        row = c.fetchone()
        conn.close()
        if row:
            ct, nonce = row
            try:
                pwd = decrypt_password(ct, self.key, nonce)
                QMessageBox.information(self, f"{service}", f"Contraseña: {pwd}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo descifrar: {str(e)}")

    def copy_secret(self, item):
        service = item.text().split(" ")[0]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password, nonce FROM secrets WHERE service=?", (service,))
        row = c.fetchone()
        conn.close()
        if row:
            ct, nonce = row
            pwd = decrypt_password(ct, self.key, nonce)
            QApplication.clipboard().setText(pwd)
            QMessageBox.information(self, "Copiado", "Contraseña copiada al portapapeles")

    def edit_secret(self, item):
        # Aquí puedes abrir un diálogo para editar los campos
        QMessageBox.information(self, "Editar", "Funcionalidad de edición pendiente de implementación")

    # ----------------------------
    # Dashboard
    # ----------------------------
    def update_dashboard(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password, nonce FROM secrets WHERE deleted=0")
        rows = c.fetchall()
        total = len(rows)
        weak_count = 0
        for row in rows:
            pwd = decrypt_password(row[0], self.key, row[1])
            if password_strength(pwd) < 80:
                weak_count += 1
        self.dashboard_label.setText(f"Dashboard - Total registros: {total} | Contraseñas débiles: {weak_count}")
        conn.close()

    def clear_inputs(self):
        self.service_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.pbar.setValue(0)
        self.strength_label.setText("Seguridad: N/A")

# ----------------------------
# Ejecución
# ----------------------------
def main():
    app = QApplication(sys.argv)
    window = PassGuardian()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()




