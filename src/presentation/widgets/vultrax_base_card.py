from PyQt5.QtWidgets import QFrame, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from src.presentation.theme_manager import ThemeManager

class VultraxBaseCard(QFrame):
    """
    Standard Base Card for Vultrax Core Design System.
    Implements 12-column grid compatibility and token-based styling.
    """
    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VultraxCard")
        self.setFrameShape(QFrame.NoFrame)
        
        # Standard layout for all cards
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)
        
        # NOTE: Do NOT call refresh_styles here. Subclasses must call it
        # AFTER _setup_ui() to ensure all tactical indicators are defined.

    def refresh_styles(self):
        """Card styling delegated to QSS (dashboard.qss) using tokens."""
        # Polishing ensures the QSS rules are reapplied when properties change
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
