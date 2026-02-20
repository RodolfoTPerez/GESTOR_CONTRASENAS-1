from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
from src.presentation.theme_manager import ThemeManager

class HealthReactorWidget(QWidget):
    """
    HUD-style Health Reactor.
    Displays security score with dynamic neon arcs and ghost transparency.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self.health_score = 100
        self.theme = ThemeManager()
        # Initialize color from theme success (standard for 100 health)
        colors = self.theme.get_theme_colors()
        self.primary_color = QColor(colors.get("success", "#10b981"))

    def set_data(self, score):
        self.health_score = int(score)
        colors = self.theme.get_theme_colors()
        if self.health_score < 60: self.primary_color = QColor(colors.get("danger", "#ef4444"))
        elif self.health_score < 85: self.primary_color = QColor(colors.get("warning", "#f59e0b"))
        else: self.primary_color = QColor(colors.get("success", "#10b981"))
        self.update()

    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        is_ghost = self.property("ghost") == "true"
        dimmer = getattr(self.theme, '_GLOBAL_OPACITY', 1.0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(12, 12, -12, -12)
        center = rect.center()
        width = 12
        
        # 1. TACTICAL HEXAGON-ISH BACKGROUND (Concave Effect)
        bg_col = QColor(colors.get("card_bg", "rgba(15, 23, 42, 0.4)"))
        bg_col.setAlpha(int(30 * dimmer))
        painter.setBrush(QBrush(bg_col))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, self.width()/2 - 10, self.height()/2 - 10)

        # 2. BACKGROUND TRACK (Tenue)
        track_col = QColor(colors.get("text_dim", "#94a3b8"))
        track_col.setAlpha(int(40 * dimmer))
        painter.setPen(QPen(track_col, width, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225 * 16, -270 * 16)
        
        # 3. MULTI-LAYERED ACTIVE ARC (HIFI NEON)
        color = QColor(self.primary_color)
        span = int((self.health_score / 100.0) * 270 * 16)
        start_angle = 225 * 16
        
        # Layer A: Massive Outer Bloom
        glow_1 = QColor(color)
        glow_1.setAlpha(int(40 * dimmer))
        painter.setPen(QPen(glow_1, width * 1.8, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, start_angle, -span)
        
        # Layer B: Focused Core Glow
        glow_2 = QColor(color)
        glow_2.setAlpha(int(90 * dimmer))
        painter.setPen(QPen(glow_2, width * 1.6, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, start_angle, -span)

        # Layer C: Primary Arc
        core_col = QColor(color)
        core_col.setAlpha(int(220 * dimmer))
        painter.setPen(QPen(core_col, width, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, start_angle, -span)

        # 4. CENTER HUD (Refined Stats)
        painter.setPen(Qt.NoPen)
        
        # Main Score
        font_score = QFont("Consolas", 28, QFont.Bold)
        painter.setFont(font_score)
        text_color = QColor(colors["text"])
        text_color.setAlpha(int(230 * dimmer))
        painter.setPen(text_color)
        # Perfectly centered in the middle of the widget
        painter.drawText(self.rect(), Qt.AlignCenter, str(self.health_score))

