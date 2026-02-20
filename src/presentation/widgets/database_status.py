from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient
import math
from src.presentation.theme_manager import ThemeManager

class CloudDatabaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._online = False
        self._pulse_phase = 0
        self.theme = ThemeManager()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.setInterval(30)
        
    def setOnline(self, online: bool):
        self._online = online
        if not self._timer.isActive(): self._timer.start()
        self.update()
    
    def refresh_theme(self):
        self.theme = ThemeManager()
        self.update()

    def _pulse(self):
        self._pulse_phase = (self._pulse_phase + 0.02) % 1.0
        self.update()
    
    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        # [SENIOR FIX] Respect global dimmer
        dimmer = getattr(self.theme, '_GLOBAL_OPACITY', 1.0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center_x, center_y = self.width() / 2, self.height() / 2
        
        # SUPABASE = THEME SECONDARY (Cyan/Blue variant)
        if self._online:
            db_color = QColor(colors["secondary"]) 
        else:
            db_color = QColor(colors["text_dim"]) # Muted Grey
            
        pulse_factor = (math.sin(self._pulse_phase * 2 * math.pi) + 1) / 2 # Normalize to 0-1
        
        # 1. Glow Pulse (Behind the icon - 10% for Ghost)
        if self._online:
            is_ghost = self.property("ghost") == "true"
            glow_radius = 12 + 7 * pulse_factor
            gradient = QRadialGradient(center_x, center_y, glow_radius)
            # Higher opacity for the glow center
            glow_alpha = int(76 * pulse_factor) if is_ghost else int(100 * pulse_factor) # Senior: Increased from 25
            glow_alpha = int(glow_alpha * dimmer)
            
            # [FIX] Use theme-aware secondary color for glow
            c = db_color
            gradient.setColorAt(0, QColor(c.red(), c.green(), c.blue(), glow_alpha))
            gradient.setColorAt(1, Qt.transparent)
            painter.setPen(Qt.NoPen); painter.setBrush(gradient)
            painter.drawEllipse(QRectF(center_x - glow_radius, center_y - glow_radius, glow_radius * 2, glow_radius * 2))
        
        # 2. Cloud DB Icon (Double Ring Design - 40% for Ghost)
        is_ghost = self.property("ghost") == "true"
        if is_ghost: 
            db_color.setAlpha(int(178 * dimmer)) # 70% HUD translucency (Senior: Increased from 40%)
        else:
            db_color.setAlpha(int(255 * dimmer))
        
        pen = QPen(db_color, 2); painter.setPen(pen); painter.setBrush(Qt.NoBrush)
        # Intensity boost if online
        if self._online:
            pen.setWidthF(2.2)
            painter.setPen(pen)
            
        # Top ring
        painter.drawEllipse(QRectF(center_x - 8, center_y - 11, 16, 4))
        # Middle ring 
        painter.drawArc(int(center_x - 8), int(center_y - 2), 16, 4, 0, 360 * 16)
        # Vertical lines
        painter.drawLine(int(center_x - 8), int(center_y - 9), int(center_x - 8), int(center_y + 9))
        painter.drawLine(int(center_x + 8), int(center_y - 9), int(center_x + 8), int(center_y + 9))
        # Bottom curve
        painter.drawArc(int(center_x - 8), int(center_y + 7), 16, 4, 180 * 16, 180 * 16)
        
        # 3. Status Dot (Pulsing size and glow)
        dot_x, dot_y = center_x + 8, center_y - 10
        dot_color = db_color if self._online else QColor(colors["danger"])
        
        # Dot Glow (10% for Ghost)
        dot_glow_radius = 5 + 5 * pulse_factor
        dot_gradient = QRadialGradient(dot_x, dot_y, dot_glow_radius)
        dot_glow_alpha = int(102 * pulse_factor) if is_ghost else int(180 * pulse_factor) # Senior: Increased from 40
        dot_glow_alpha = int(dot_glow_alpha * dimmer)
        
        dot_gradient.setColorAt(0, QColor(dot_color.red(), dot_color.green(), dot_color.blue(), dot_glow_alpha))
        dot_gradient.setColorAt(1, Qt.transparent)
        painter.setBrush(dot_gradient); painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(dot_x - dot_glow_radius, dot_y - dot_glow_radius, dot_glow_radius * 2, dot_glow_radius * 2))
        
        # Actual Dot Core (80% for Ghost)
        dot_size = 4.5 + 2 * pulse_factor
        if is_ghost: 
            dot_color.setAlpha(int(204 * dimmer)) # Senior: Increased from 102
        else:
            dot_color.setAlpha(int(255 * dimmer))
            
        painter.setBrush(dot_color); painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(dot_x - dot_size/2, dot_y - dot_size/2, dot_size, dot_size))

class LocalDatabaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._online = False
        self._pulse_phase = 0
        self.theme = ThemeManager()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.setInterval(40)
        
    def setOnline(self, online: bool):
        self._online = online
        if not self._timer.isActive(): self._timer.start()
        self.update()
    
    def refresh_theme(self):
        self.theme = ThemeManager()
        self.update()

    def _pulse(self):
        self._pulse_phase = (self._pulse_phase + 0.02) % 1.0
        self.update()
    
    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        # [SENIOR FIX] Respect global dimmer
        dimmer = getattr(self.theme, '_GLOBAL_OPACITY', 1.0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center_x, center_y = self.width() / 2, self.height() / 2
        
        # SQLITE = GREEN (#10b981 / success)
        db_color = QColor(colors["success"]) if self._online else QColor(colors["text_dim"])
        pulse_factor = (math.sin(self._pulse_phase * 2 * math.pi) + 1) / 2 # Normalize to 0-1

        # 1. Glow Pulse (10% for Ghost)
        is_ghost = self.property("ghost") == "true"
        if self._online:
            glow_radius = 12 + 5 * pulse_factor
            gradient = QRadialGradient(center_x, center_y, glow_radius)
            glow_alpha = int(76 * pulse_factor) if is_ghost else int(80 * pulse_factor) # Senior: Increased from 25
            glow_alpha = int(glow_alpha * dimmer)
            
            gradient.setColorAt(0, QColor(db_color.red(), db_color.green(), db_color.blue(), glow_alpha))
            gradient.setColorAt(1, Qt.transparent)
            painter.setPen(Qt.NoPen); painter.setBrush(gradient)
            painter.drawEllipse(QRectF(center_x - glow_radius, center_y - glow_radius, glow_radius * 2, glow_radius * 2))

        # 2. Local Icon (Double Ring Design - 40% for Ghost)
        if is_ghost: 
            db_color.setAlpha(int(178 * dimmer))
        else:
            db_color.setAlpha(int(255 * dimmer))
            
        pen = QPen(db_color, 2); painter.setPen(pen); painter.setBrush(Qt.NoBrush)
        # Top ring
        painter.drawEllipse(QRectF(center_x - 8, center_y - 11, 16, 4))
        # Middle ring
        painter.drawArc(int(center_x - 8), int(center_y - 2), 16, 4, 0, 360 * 16)
        # Vertical lines
        painter.drawLine(int(center_x - 8), int(center_y - 9), int(center_x - 8), int(center_y + 9))
        painter.drawLine(int(center_x + 8), int(center_y - 9), int(center_x + 8), int(center_y + 9))
        # Bottom curve
        painter.drawArc(int(center_x - 8), int(center_y + 7), 16, 4, 180 * 16, 180 * 16)
        
        # 3. Status Dot
        dot_x, dot_y = center_x + 7, center_y - 10
        dot_color = db_color if self._online else QColor(colors["danger"])
        
        # Dot Glow (10% for Ghost)
        dot_glow_radius = 4 + 4 * pulse_factor
        dot_gradient = QRadialGradient(dot_x, dot_y, dot_glow_radius)
        dot_glow_alpha = int(102 * pulse_factor) if is_ghost else int(150 * pulse_factor) # Senior: Increased from 35
        dot_glow_alpha = int(dot_glow_alpha * dimmer)
        
        dot_gradient.setColorAt(0, QColor(dot_color.red(), dot_color.green(), dot_color.blue(), dot_glow_alpha))
        dot_gradient.setColorAt(1, Qt.transparent)
        painter.setBrush(dot_gradient); painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(dot_x - dot_glow_radius, dot_y - dot_glow_radius, dot_glow_radius * 2, dot_glow_radius * 2))

        # Core Dot (80% for Ghost)
        dot_size = 4 + 1.5 * pulse_factor
        if is_ghost: 
            dot_color.setAlpha(int(204 * dimmer)) # Senior: Increased from 102
        else:
            dot_color.setAlpha(int(255 * dimmer))
            
        painter.setBrush(dot_color); painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(dot_x - dot_size/2, dot_y - dot_size/2, dot_size, dot_size))
