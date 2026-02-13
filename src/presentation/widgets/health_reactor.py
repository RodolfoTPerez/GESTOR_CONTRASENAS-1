from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(8, 8, -8, -8)
        width = 10
        
        # 1. Background Track
        # Use a theme-aware track color (faint border or dim text dimmed further)
        track_col = QColor(colors.get("border", "#1e293b"))
        track_col.setAlpha(40) 
        painter.setPen(QPen(track_col, width, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, -45 * 16, 270 * 16)
        
        # 2. Active Gauge Arc
        is_ghost = self.property("ghost") == "true"
        color = QColor(self.primary_color)
        
        pen_color = QColor(self.primary_color)
        if is_ghost: pen_color.setAlpha(204) # 80% Vibrant Arc (Senior: Increased from 60%)
        pen = QPen(pen_color, width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        
        span = int((self.health_score / 100.0) * 270 * 16)
        painter.drawArc(rect, 225 * 16, -span)

        # 3. Center Text
        painter.setPen(Qt.NoPen)
        font_score = QFont("Segoe UI", 26, QFont.Bold)
        painter.setFont(font_score)
        
        # [FIX] Use Theme Text Color instead of hardcoded white
        text_color = QColor(colors["text"])
        if is_ghost: text_color.setAlpha(204) # 80% Center Score
        painter.setPen(text_color)
        
        number_rect = QRectF(0, 30, self.width(), 45)
        painter.drawText(number_rect, Qt.AlignCenter, str(self.health_score))
        
        # Subtitle "SCORE"
        font_sub = QFont("Segoe UI", 8, QFont.Bold)
        font_sub.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        painter.setFont(font_sub)
        
        # [FIX] Use Theme Dim Color
        sub_color = QColor(colors["text_dim"])
        if is_ghost: sub_color.setAlpha(128) # 50% Metadata label (Senior: Increased from 30%)
        painter.setPen(sub_color)
        
        sub_rect = QRectF(0, 75, self.width(), 20)
        painter.drawText(sub_rect, Qt.AlignCenter, "SCORE")
