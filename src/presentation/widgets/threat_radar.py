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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = ThemeManager()
        self._values = [80, 70, 90, 60, 85, 75, 70, 80]
        self.sweep_angle = 0
        self.setMinimumSize(140, 140)
        
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
            event.accept()
        super().mouseReleaseEvent(event)

    def _rotate_sweep(self):
        self.sweep_angle = (self.sweep_angle + 3) % 360
        self.update()

    def setValues(self, values: list):
        if len(values) == 8:
            self._values = values
            self.update()

    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        is_ghost = self.property("ghost") == "true"
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = QPointF(self.width() / 2, self.height() / 2 + 10)
        radius = min(self.width(), self.height()) / 2 * 0.55
        num_vars = len(self._values)
        angle_step = 2 * math.pi / num_vars

        # 1. SCANNER BACKGROUND (Premium HUD)
        bg_col = QColor(colors["bg_dashboard_card"])
        if is_ghost: bg_col.setAlpha(40)
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(QColor(colors.get("border", "rgba(255,255,255,0.1)")), 1))
        painter.drawEllipse(center, radius + 15, radius + 15)

        # Concentric rings & Grid
        grid_col = QColor(colors.get("text_dim", "#94a3b8"))
        grid_col.setAlpha(60)
        painter.setPen(QPen(grid_col, 0.5, Qt.DashLine))
        for i in range(1, 4):
            r = radius * (i / 3)
            painter.drawEllipse(center, r, r)

        # Radial Spokes
        for j in range(num_vars):
            angle = j * angle_step - math.pi / 2
            painter.drawLine(center, QPointF(center.x() + radius * math.cos(angle), center.y() + radius * math.sin(angle)))

        # 2. ANIMATED SWEEP (High-Fidelity Sonar)
        sweep_grad = QConicalGradient(center, -self.sweep_angle)
        primary = QColor(colors.get("primary", "#3b82f6"))
        alpha_main = 180 if not is_ghost else 120
        sweep_grad.setColorAt(0, QColor(primary.red(), primary.green(), primary.blue(), alpha_main))
        sweep_grad.setColorAt(0.1, QColor(primary.red(), primary.green(), primary.blue(), alpha_main // 2))
        sweep_grad.setColorAt(0.3, Qt.transparent)
        
        painter.setBrush(QBrush(sweep_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)

        # 3. DATA POLYGON (Tactical Area)
        poly_data = QPolygonF()
        for j in range(num_vars):
            val = self._values[j] / 100.0
            angle = j * angle_step - math.pi / 2
            poly_data.append(QPointF(center.x() + radius * val * math.cos(angle), center.y() + radius * val * math.sin(angle)))

        fill_color = QColor(colors.get("ai_sec", colors.get("warning", "#f59e0b"))) 
        fill_alpha = 100 if not is_ghost else 60
        fill_color.setAlpha(fill_alpha)
        
        painter.setBrush(QBrush(fill_color))
        border_col = QColor(colors.get("primary", "#3b82f6"))
        if is_ghost: border_col.setAlpha(200)
        painter.setPen(QPen(border_col, 2))
        painter.drawPolygon(poly_data)

        # 4. GLOWING VERTICES
        painter.setBrush(QBrush(border_col))
        painter.setPen(Qt.NoPen)
        for i in range(poly_data.count()):
            p = poly_data.at(i)
            painter.drawEllipse(p, 3, 3)

        # 5. LABELS & HUD OVERLAY
        title_col = QColor(colors.get("text_dim", "#94a3b8"))
        painter.setPen(title_col)
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(10, 10, "RADAR: ACTIVE")

        # Static Grid ID
        painter.setFont(QFont("Consolas", 6))
        painter.drawText(self.width() - 60, 10, "GRID_V2.0")

        label_col = QColor(colors.get("text", "#ffffff"))
        if is_ghost: label_col.setAlpha(180)
        painter.setPen(label_col)
        painter.setFont(QFont("Consolas", 7, QFont.Bold))
        for j in range(num_vars):
            angle = j * angle_step - math.pi / 2
            label_r = radius + 22
            lx = center.x() + label_r * math.cos(angle)
            ly = center.y() + label_r * math.sin(angle)
            
            lbl = self._labels[j]
            rect = QRectF(lx - 35, ly - 8, 70, 16)
            
            # Smart alignment
            if abs(math.cos(angle)) < 0.1: # Vertical
                rect.moveCenter(QPointF(lx, ly + (10 if math.sin(angle) > 0 else -10)))
            
            painter.drawText(rect, Qt.AlignCenter, lbl)
