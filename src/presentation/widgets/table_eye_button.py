from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QTimer

class TableEyeButton(QPushButton):
    """
    Eye toggle button for password fields in tables.
    Includes auto-hide timer for enhanced security.
    """
    def __init__(self, row, callback_show, callback_hide, parent=None):
        super().__init__("👁️", parent)
        self.row_index = row
        self.callback_show = callback_show
        self.callback_hide = callback_hide
        self.setFlat(True)
        self.setObjectName("table_eye_btn")
        self.setFixedSize(30, 30) 
        self.setCursor(Qt.PointingHandCursor)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._auto_hide)
        self.clicked.connect(self._toggle)

    def _toggle(self):
        if self.text() == "👁️":
            self.setText("🙈")
            self.callback_show(self) 
            self.timer.start(2500) # Auto-hide after 2.5s
        else:
            self._auto_hide()

    def _auto_hide(self):
        self.setText("👁️")
        self.callback_hide(self)
