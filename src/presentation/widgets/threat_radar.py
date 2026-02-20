from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF, QFont, QBrush, QConicalGradient, QLinearGradient
import math
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class ThreatRadarWidget(QWidget):
    """
    Tactical Animated Sonar Radar
    Includes scan line animation and internal progress metrics.
    """
    clicked = pyqtSignal()
    doubleClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = ThemeManager()
        self._values = [80, 70, 90, 60, 85, 75, 70, 80]
        self.sweep_angle = 0
        self.setMinimumSize(200, 200)
        
        self.retranslateUi()
        
        # [FIX] Animation Timer for Sweep (Sonar effect) - Starts automatically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate_sweep)
        self.timer.start(30) # 33 FPS for smooth sweep
        
    def retranslateUi(self):
        """Localized Labels for Radar Sectors"""
        try:
            self._labels = MESSAGES.LISTS.RADAR_LABELS
            self.update()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in ThreatRadarWidget: {e}")
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def _rotate_sweep(self):
        # [SENIOR ANIMATION] Increased smoothness for sweep
        self.sweep_angle = (self.sweep_angle + 2.5) % 360
        self.update()

    def setValues(self, values: list):
        if len(values) == 8:
            self._values = values
            self.update()

    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        is_ghost = self.property("ghost") == "true"
        dimmer = getattr(self.theme, '_GLOBAL_OPACITY', 1.0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # [REFIX] Perfectly centered to avoid bottom clipping
        center = QPointF(self.width() / 2, self.height() / 2)
        # Radius adjusted to leave a wide perimeter for HUD text and labels
        radius = min(self.width(), self.height()) / 2 - 70
        num_vars = len(self._values)
        angle_step = 2 * math.pi / num_vars
        
        # ... drawing scanner bg, rings, sweep, polygon ...
        
        # (Assuming the drawing code is hidden but the context is same)
        
        # 5. LABELS & HUD OVERLAY (Refined Typography)
        # Using tiny font for HUD
        painter.setFont(self.theme.get_font("tiny"))
        metrics = painter.fontMetrics()
        
        hud_text = "TACTICAL RADAR: LIVE"
        # [REFIX] Centered horizontally and lowered to the absolute bottom
        hud_w = metrics.width(hud_text)
        painter.setPen(QColor(colors.get("text_dim", "#94a3b8")))
        painter.drawText(int((self.width() - hud_w) / 2), self.height() - 5, hud_text)

        label_col = QColor(colors.get("text", "#ffffff"))
        label_col.setAlpha(int(200 * dimmer))
        painter.setPen(label_col)
        
        for j in range(num_vars):
            angle = j * angle_step - math.pi / 2
            label_r = radius + 30 # Reduced padding to avoid clipping
            lx = center.x() + label_r * math.cos(angle)
            ly = center.y() + label_r * math.sin(angle)
            
            lbl = self._labels[j]
            text_w = metrics.width(lbl)
            text_h = metrics.height()
            
            # Smart Rectangle based on metrics
            rect = QRectF(lx - text_w / 2, ly - text_h / 2, text_w, text_h)
            
            # Absolute boundary check to prevent ANY clipping
            if rect.left() < 2: rect.moveLeft(2)
            if rect.right() > self.width() - 2: rect.moveRight(self.width() - 2)
            if rect.top() < 2: rect.moveTop(2)
            if rect.bottom() > self.height() - 2: rect.moveBottom(self.height() - 2)
            
            painter.drawText(rect, Qt.AlignCenter, lbl)
