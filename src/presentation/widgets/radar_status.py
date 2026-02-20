from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QConicalGradient, QRadialGradient
import math

class RadarStatusWidget(QWidget):
    """
    Minimal radar-style online status indicator for Dark Mode SaaS dashboard.
    - Circular radar with very subtle outline (low opacity).
    - Single thin scanning line rotating slowly (one full rotation every 4–6 seconds).
    - Color when online: electric blue or neon green with soft glow.
    - Background transparent.
    - No flashing, no fast motion, no aggressive effects.
    - When offline: stop rotation and change to muted dark grey or subtle red.
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._online = False
        self._angle = 0  # Current rotation angle
        self._pulse_phase = 0  
        
        from src.presentation.theme_manager import ThemeManager
        self.theme_manager = ThemeManager()
        
        # Animation timer (slow rotation: 5 seconds per full rotation)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(20)  # Update every 20ms for smooth animation
        self._timer.start()  # Start immediately as requested
        
    def setOnline(self, online: bool):
        """Set online status and ensure animation is running"""
        self._online = online
        if not self._timer.isActive():
            self._timer.start()
        self.update()
    
    def refresh_theme(self):
        """Re-loads colors from settings/theme manager"""
        from src.presentation.theme_manager import ThemeManager
        self.theme_manager = ThemeManager()
        self.update()
    
    def _rotate(self):
        """Rotate the scanning line and update pulse phase"""
        # Significant increment for visible motion
        self._angle = (self._angle + 2) % 360
        if not hasattr(self, "_pulse_phase"): self._pulse_phase = 0
        self._pulse_phase = (self._pulse_phase + 0.02) % 1.0
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(self.width(), self.height()) / 2 - 4
        
        colors = self.theme_manager.get_theme_colors()
        # [SENIOR FIX] Respect global dimmer
        dimmer = getattr(self.theme_manager, '_GLOBAL_OPACITY', 1.0)
        
        # Colors based on health
        if self._online:
            base_color = QColor(colors["success"]) 
            line_opacity = 200
            circle_opacity = 30
        else:
            base_color = QColor(colors["danger"]) 
            line_opacity = 180
            circle_opacity = 40
            
        # 1. Draw outer circle
        is_ghost = self.property("ghost") == "true"
        if is_ghost:
            line_opacity = int(line_opacity * 0.85) 
            circle_opacity = int(0.25 * 255) 
            
        # Apply global dimmer
        line_opacity = int(line_opacity * dimmer)
        circle_opacity = int(circle_opacity * dimmer)

        pen = QPen(QColor(base_color.red(), base_color.green(), base_color.blue(), circle_opacity), 1.5)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2))
        
        # 2. Draw Scanning Effect (The Pie)
        start_angle = int((90 - self._angle) * 16)
        span_angle = 45 * 16 
        
        gradient = QConicalGradient(center_x, center_y, 90 - self._angle)
        gradient.setColorAt(0, QColor(base_color.red(), base_color.green(), base_color.blue(), line_opacity))
        gradient.setColorAt(0.1, QColor(base_color.red(), base_color.green(), base_color.blue(), int(50 * dimmer)))
        gradient.setColorAt(0.3, Qt.transparent)
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawPie(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2), 
                       start_angle, span_angle)

        # 3. Draw the main leading line (High contrast)
        lead_pen = QPen(QColor(base_color.red(), base_color.green(), base_color.blue(), line_opacity), 2)
        painter.setPen(lead_pen)
        angle_rad = math.radians(self._angle - 90)
        lx = center_x + radius * math.cos(angle_rad)
        ly = center_y + radius * math.sin(angle_rad)
        painter.drawLine(int(center_x), int(center_y), int(lx), int(ly))
        
        # 4. Center Dot
        # Fix dot opacity too
        dot_col = QColor(base_color)
        dot_col.setAlpha(int(255 * dimmer))
        painter.setBrush(dot_col)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(center_x - 2, center_y - 2, 4, 4))

        # --- RANDOM RADAR BLIPS (Popping appearing/disappearing) ---
        # Initialize blips list if it doesn't exist
        if not hasattr(self, "_blips"):
            self._blips = [] # List of (x, y, opacity)
            
        # Occasionally add a new blip (low probability)
        import random
        if len(self._blips) < 3 and random.random() < 0.05:
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(5, radius - 5)
            bx = center_x + dist * math.cos(angle)
            by = center_y + dist * math.sin(angle)
            self._blips.append({"pos": (bx, by), "life": 1.0}) 
            
        # Update and draw blips
        new_blips = []
        for blip in self._blips:
            life = blip["life"]
            bx, by = blip["pos"]
            
            # Draw the blip (fading dot - 80% for Ghost)
            blip_opacity = int(255 * life * 0.8) if is_ghost else int(255 * life)
            blip_opacity = int(blip_opacity * dimmer)
            
            painter.setBrush(QColor(base_color.red(), base_color.green(), base_color.blue(), blip_opacity))
            painter.drawEllipse(QRectF(bx - 1.5, by - 1.5, 3, 3))
            
            # Subtle glow for the blip (40% for Ghost)
            glow_alpha_blip = int(60 * life * 0.4) if is_ghost else int(60 * life)
            glow_alpha_blip = int(glow_alpha_blip * dimmer)
            
            painter.setBrush(QColor(base_color.red(), base_color.green(), base_color.blue(), glow_alpha_blip))
            painter.drawEllipse(QRectF(bx - 3, by - 3, 6, 6))
            
            
            # Decrease life
            blip["life"] -= 0.02
            if blip["life"] > 0:
                new_blips.append(blip)
        self._blips = new_blips
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
