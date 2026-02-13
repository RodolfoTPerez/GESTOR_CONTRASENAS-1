from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont
import math
from src.presentation.theme_manager import ThemeManager

class StatusBadgeWidget(QWidget):
    def __init__(self, icon_char, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.icon_char = icon_char
        self.status_type = "OK"
        self._pulse_phase = 0
        self._rotation = 0
        self._syncing = False
        self.theme = ThemeManager()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.setInterval(30); self._timer.start()
        
    def setSyncing(self, syncing: bool):
        self._syncing = syncing
        if not syncing: self._pulse_phase = 0
        self.update()

    def setStatus(self, label_text_ignored, status_type="OK"):
        self.status_type = status_type
        self.update()
        
    def refresh_theme(self):
        self.theme = ThemeManager()
        self.update()

    def _animate(self):
        self._pulse_phase = (self._pulse_phase + 0.015) % 1.0
        if self._syncing:
            self._rotation = (self._rotation + 8) % 360
        self.update()
        
    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.status_type == "OK": c = QColor(colors["success"])
        elif self.status_type == "WARNING": c = QColor(colors["warning"])
        elif self.status_type == "ERROR": c = QColor(colors["danger"])
        else: c = QColor(colors["text_dim"])
            
        # [NEON SHIELD OVERRIDE]
        if self.icon_char == "🛡️" and self.status_type == "OK":
            c = QColor("#00ff99") # Ultra-vibrant Neon Green for the shield
            
        is_ghost = self.property("ghost") == "true"
        pulse_val = math.sin(self._pulse_phase * 2 * math.pi) if self._syncing else 0
        if self.status_type != "OK" or self._syncing:
            glow_opacity = 50 if self.status_type == "ERROR" else (int(40 + 40 * pulse_val) if self._syncing else 20)
            if is_ghost: glow_opacity = int(glow_opacity * 0.5) 
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), glow_opacity))
            painter.setPen(Qt.NoPen); painter.drawEllipse(QRectF(8, 8, 24, 24))
            
        painter.setFont(QFont("Segoe UI Symbol", 16))
        icon_opacity = 255 if self.status_type == "ERROR" else (int(180 + 75 * pulse_val) if self._syncing else 140)
        if is_ghost: icon_opacity = int(icon_opacity * 0.85) 
        painter.setPen(QColor(c.red(), c.green(), c.blue(), icon_opacity))
        
        # [SYNC ROTATION]
        if self.icon_char == "🔄" and self._syncing:
            painter.translate(self.width()/2, self.height()/2)
            painter.rotate(self._rotation)
            painter.drawText(QRectF(-20, -20, 40, 40), Qt.AlignCenter, self.icon_char)
        else:
            painter.drawText(self.rect(), Qt.AlignCenter, self.icon_char)
