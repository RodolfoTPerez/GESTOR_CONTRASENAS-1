from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        margin = min(width, height) * 0.08
        side = min(width, height) - margin
        rect = self.rect()
        
        from PyQt5.QtCore import QRectF
        arc_rect = QRectF(
            (width - side) / 2, 
            (height - side) / 2, 
            side, 
            side
        )

        stroke_width = side * 0.09
        font_size = int(side * 0.20)

        # 1. Background Ring
        bg_color = QColor(colors["text_dim"])
        bg_color.setAlpha(80) # Increased opacity
        pen_bg = QPen(bg_color)
        pen_bg.setWidthF(stroke_width)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        
        inner_rect = arc_rect.adjusted(stroke_width/2, stroke_width/2, -stroke_width/2, -stroke_width/2)
        painter.drawArc(inner_rect, 0, 360 * 16)

        # 2. Dynamic Color (Professional)
        is_ghost = self.property("ghost") == "true"
        if self._value < 40: 
            color = QColor(colors["danger"])
        elif self._value < 75: 
            color = QColor(colors["warning"])
        else: 
            color = QColor(colors["success"])
        
        if is_ghost: 
            # Fills use GLASSY alpha (HUD Standard)
            is_urgent = (color.red() > 200)
            alpha = int(0.15 * 255) if is_urgent else int(0.08 * 255)
            color.setAlpha(alpha)

        # 3. Progress Arc with SOFT Glow
        span_angle = int(-(self._value / 100.0) * 360 * 16)
        
        # Outer soft glow
        glow_c1 = QColor(color)
        glow_c1.setAlpha(25)
        pen_g1 = QPen(glow_c1)
        pen_g1.setWidthF(stroke_width * 1.8)
        pen_g1.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_g1)
        painter.drawArc(inner_rect, 90 * 16, span_angle)
        
        # Inner soft glow
        glow_c2 = QColor(color)
        glow_c2.setAlpha(50)
        pen_g2 = QPen(glow_c2)
        pen_g2.setWidthF(stroke_width * 1.3)
        pen_g2.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_g2)
        painter.drawArc(inner_rect, 90 * 16, span_angle)

        # Main Progress (Neon Glow-Glass Border)
        pen_color = QColor(color)
        if is_ghost: pen_color.setAlpha(int(0.65 * 255)) 
        pen_progress = QPen(pen_color)
        pen_progress.setWidthF(stroke_width)
        pen_progress.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_progress)
        painter.drawArc(inner_rect, 90 * 16, span_angle)

        # 4. Central Text (NEON HUD VIBRANCY - 60% for true Ghost)
        text_color = QColor(colors["text"])
        if is_ghost: text_color.setAlpha(153) # 60% opacity
        painter.setPen(text_color)
        font = QFont("Consolas", font_size, QFont.Bold)
        painter.setFont(font)
        
        value_rect = QRectF(
            arc_rect.left(), 
            arc_rect.top() + arc_rect.height() * 0.35, 
            arc_rect.width(), 
            arc_rect.height() * 0.3
        )
        painter.drawText(value_rect, Qt.AlignCenter, f"{self._value}")
        
        # Subtitle (Tenue pero visible 'adelante' - 30%)
        font_sub = QFont("Consolas", int(font_size * 0.35), QFont.DemiBold)
        painter.setFont(font_sub)
        sub_color = QColor(colors["text"])
        if is_ghost: sub_color.setAlpha(76) # 30% alpha for subtitle
        painter.setPen(sub_color)
        
        sub_rect = QRectF(
            arc_rect.left(), 
            arc_rect.top() + arc_rect.height() * 0.58, 
            arc_rect.width(), 
            arc_rect.height() * 0.2
        )
        painter.drawText(sub_rect, Qt.AlignCenter, "SCORE")
