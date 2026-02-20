from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QRadialGradient, QBrush
from src.presentation.theme_manager import ThemeManager

class CircularGauge(QWidget):
    """
    Professional Security Score Gauge
    Soft neon accents - Dynamic theming enabled.
    """
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.setMinimumSize(140, 140)
        self.theme = ThemeManager()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        super().mouseReleaseEvent(event)

    @pyqtProperty(int)
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = max(0, min(100, val))
        self.update()

    def refresh_theme(self):
        """Re-loads colors from settings/theme manager"""
        from src.presentation.theme_manager import ThemeManager
        self.theme = ThemeManager()
        self.update()

    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        is_ghost = self.property("ghost") == "true"
        dimmer = getattr(self.theme, '_GLOBAL_OPACITY', 1.0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height) * 0.85
        center = QPointF(width / 2, height / 2)
        
        from PyQt5.QtCore import QRectF
        arc_rect = QRectF(
            (width - side) / 2, 
            (height - side) / 2, 
            side, 
            side
        )

        stroke_width = side * 0.08
        font_size = int(side * 0.22)

        # 1. RADIAL BACKGROUND (Concave HUD Effect)
        bg_grad = QRadialGradient(center, side / 2)
        bg_col = QColor(colors.get("card_bg", "rgba(15, 23, 42, 0.4)"))
        bg_col.setAlpha(int(40 * dimmer))
        bg_grad.setColorAt(0, Qt.transparent)
        bg_grad.setColorAt(1, bg_col)
        
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, side / 2 + 5, side / 2 + 5)

        # 2. TACTICAL TICKS (Mechanical Detail)
        tick_col = QColor(colors.get("text_dim", "#94a3b8"))
        tick_col.setAlpha(int(80 * dimmer))
        painter.setPen(QPen(tick_col, 1))
        
        for i in range(60):
            angle = i * 6
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            length = 5 if i % 5 == 0 else 2
            alpha = int(150 * dimmer) if i % 5 == 0 else int(60 * dimmer)
            tick_col.setAlpha(alpha)
            painter.setPen(QPen(tick_col, 1.2 if i % 5 == 0 else 0.8))
            painter.drawLine(0, int(-side/2 - 2), 0, int(-side/2 - 2 - length))
            painter.restore()

        # 3. DYNAMIC COLOR SELECTION
        if self._value < 40: 
            color = QColor(colors["danger"])
        elif self._value < 75: 
            color = QColor(colors["warning"])
        else: 
            color = QColor(colors["success"])
        
        # 4. MULTI-LAYERED NEON GLOW (HIFI-CORE)
        inner_rect = arc_rect.adjusted(stroke_width/2, stroke_width/2, -stroke_width/2, -stroke_width/2)
        span_angle = int(-(self._value / 100.0) * 360 * 16)
        start_angle = 90 * 16

        # Layer A: Massive Outer Bloom
        glow_1 = QColor(color)
        glow_1.setAlpha(int(35 * dimmer))
        pen_g1 = QPen(glow_1, stroke_width * 2.2, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_g1)
        painter.drawArc(inner_rect, start_angle, span_angle)

        # Layer B: Focused Core Glow
        glow_2 = QColor(color)
        glow_2.setAlpha(int(70 * dimmer))
        pen_g2 = QPen(glow_2, stroke_width * 1.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_g2)
        painter.drawArc(inner_rect, start_angle, span_angle)

        # Layer C: Primary Visible Line
        core_col = QColor(color)
        core_col.setAlpha(int(200 * dimmer))
        pen_core = QPen(core_col, stroke_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_core)
        painter.drawArc(inner_rect, start_angle, span_angle)

        # 5. DATA HUD (Center Text)
        text_color = QColor(colors["text"])
        text_color.setAlpha(int(220 * dimmer))
        painter.setPen(text_color)
        painter.setFont(QFont("Consolas", font_size, QFont.Bold))
        
        # Perfectly centered in the middle of the widget
        painter.drawText(self.rect(), Qt.AlignCenter, str(self._value))

