from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
import math
from src.presentation.theme_manager import ThemeManager

class TimeSyncWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(115, 40)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._time_text = "00:00"
        self._status = "OK"
        self._pulse_phase = 0
        self.theme = ThemeManager()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)  
        
    def setTime(self, text: str):
        if self._time_text != text:
            self._time_text = text; self.update()
            
    def setStatus(self, status: str):
        if self._status != status:
            self._status = status; self.update()
            
    def refresh_theme(self):
        self.theme = ThemeManager()
        self.update()

    def _animate(self):
        self._pulse_phase = (self._pulse_phase + 0.015) % 1.0
        self.update()
        
    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self._status == "OK": c = QColor(colors["info"])
        elif self._status == "WARNING": c = QColor(colors["warning"])
        elif self._status == "ERROR": c = QColor(colors["danger"])
        else: c = QColor(colors["text_dim"])
            
        cy = self.height() / 2
        ix, radius = 20, 14
        
        # Clock (80% for Ghost)
        is_ghost = self.property("ghost") == "true"
        if is_ghost: c.setAlpha(204) # 80% HUD Aesthetic (Senior: Increased from 40%)
        
        painter.setPen(QPen(c, 2.0)); painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(ix - radius, cy - radius, radius*2, radius*2))
        painter.drawLine(int(ix), int(cy), int(ix), int(cy - 8))
        painter.drawLine(int(ix), int(cy), int(ix + 6), int(cy))
        
        # Pulse Dot (50% for Ghost)
        pb = math.sin(self._pulse_phase * 2 * math.pi)
        d_color = c if self._status == "OK" else QColor(colors["danger"])
        dot_alpha = int((140 + 115 * pb) * 0.5) if is_ghost else int(140 + 115 * pb) # Senior: Increased from 0.25
        painter.setBrush(QColor(d_color.red(), d_color.green(), d_color.blue(), dot_alpha))
        painter.setPen(Qt.NoPen)
        gr = 3.0 + 2.0 * pb
        painter.drawEllipse(QRectF(ix + 10 - gr, cy - 10 - gr, gr * 2, gr * 2))
        
        # Text (40% for Ghost)
        painter.setPen(c)
        font = QFont("Inter", 11, QFont.Bold); font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        painter.setFont(font)
        painter.drawText(QRectF(40, 0, 70, self.height()), Qt.AlignLeft | Qt.AlignVCenter, self._time_text)
