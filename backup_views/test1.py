from PySide6.QtWidgets import QApplication, QMainWindow, QAction
import sys

app = QApplication(sys.argv)
window = QMainWindow()
action = QAction("Test", window)
window.show()
sys.exit(app.exec())
