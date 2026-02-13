from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt, pyqtSignal

class GlassCard(QFrame):
    """
    Professional Glassmorphism Card for Dark Mode SaaS UI
    Subtle glass effect with soft shadows - Enterprise grade
    """
    doubleClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        
        # GLASSMORPHISM SUTIL - NO AGRESIVO
        # ESTILO GESTIONADO POR QSS EXTERNO (dashboard.qss)
        # Se elimina el estilo inline hardcoded para permitir theming dinámico (Cyber Arctic, etc.)
        pass
        
        # Sombra difusa profesional
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 100))  # Sombra profunda para efecto floating
        self.setGraphicsEffect(shadow)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
