from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from src.presentation.theme_manager import ThemeManager

class TacticalAtom(QLabel):
    """
    Base atomic component that connects directly to ThemeManager.
    Eliminates the need for manual font/color setting.
    """
    def __init__(self, text="", parent=None, style_token="body"):
        super().__init__(text, parent)
        self.theme = ThemeManager()
        self.style_token = style_token
        self.setObjectName(f"atom_{style_token}") # Hook for QSS
        
        # Initial Application
        self.apply_atomic_style()
        
        # subscribe to theme changes if needed, 
        # For paint-based atoms, we need explicit refresh.

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, opacity):
        self._opacity = opacity
        # Apply visual opacity
        effect = self.graphicsEffect()
        if not effect:
            from PyQt5.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        effect.setOpacity(opacity)

    _opacity = 0.99
    opacity =  pyqtProperty(float, get_opacity, set_opacity)

    def apply_atomic_style(self):
        """Applies font and base properties from ThemeManager"""
        font = self.theme.get_font(self.style_token)
        self.setFont(font)
        # Colors are handled via standard QSS where possible,
        # but for specific painter overrides we can use get_color.

class TacticalLabel(TacticalAtom):
    """Standard Label for Headers, Body, and Captions"""
    def __init__(self, text="", parent=None, token="label"):
        super().__init__(text, parent, token)

class TacticalValue(TacticalAtom):
    """Monospace Value Display for Metrics"""
    def __init__(self, text="0", parent=None, token="value"):
        super().__init__(text, parent, token)
        self.setAlignment(Qt.AlignCenter)

class TacticalTitle(TacticalAtom):
    """Card Header Title"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent, "header")
