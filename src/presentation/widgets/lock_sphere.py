import math
import random
import urllib.request
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QPainterPath, QFont, QPolygonF, QLinearGradient, QConicalGradient

from src.infrastructure.database.db_manager import DBManager
from src.infrastructure.repositories.secret_repo import SecretRepository
from src.domain.services.session_service import SessionService

logger = logging.getLogger(__name__)

class HyperRealVaultCore(QWidget):
    """
    RÉPLICA INTEGRADA: Suelo de Bóveda Hiperrealista + Esfera de Neón Intensa.
    Pantalla de Bloqueo de Seguridad para PassGuardian.
    """
    unlocked = pyqtSignal() # Señal para capturar el regreso al login
    
    def __init__(self, vault_name="VULTRAX CORE"):
        super().__init__()
        self.setWindowTitle("SECURITY LOCK")
        
        # VENTANA TRANSLÚCIDA (Cyber-Card Overlay)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Ajustamos el tamaño para permitir el centrado de la tarjeta
        self.resize(1100, 750)
        self._center_on_screen()
        
        self.vault_name = str(vault_name).upper()
        self._angle_x = 0
        self._angle_y = 0
        self._angle_step = 0.008
        self._pulse_time = 0
        self._scan_line_y = 0
        
        # Puntos de la esfera
        self.sphere_points = []
        self._generate_sphere_points()
        
        # Intentar cargar nombre real de la boveda
        self._fetch_real_vault_name()
        
        self._is_online = True
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.setInterval(20)
        self.timer.start()

        # Timer para Verificación de Conectividad (Cada 5 segundos)
        self.conn_timer = QTimer(self)
        self.conn_timer.timeout.connect(self._check_connectivity)
        self.conn_timer.start(5000)
        self._check_connectivity() 

    def _center_on_screen(self):
        screen = QDesktopWidget().screenGeometry(QDesktopWidget().cursor().pos())
        size = self.geometry()
        x = (screen.width() - size.width()) // 2 + screen.left()
        y = (screen.height() - size.height()) // 2 + screen.top()
        self.move(x, y)

    def _fetch_real_vault_name(self):
        try:
            db = DBManager("vultrax")
            cursor = db.execute("SELECT value FROM meta WHERE key = 'instance_name'")
            row = cursor.fetchone()
            if row:
                name_val = row[0]
                if isinstance(name_val, bytes):
                    name_val = name_val.decode('utf-8', errors='ignore')
                self.vault_name = str(name_val).upper()
        except Exception as e:
            logger.debug(f"Failed to fetch real vault name: {e}")

    def _check_connectivity(self):
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            self._is_online = True
        except Exception as e:
            logger.debug(f"Connectivity check failed: {e}")
            self._is_online = False

    def _generate_sphere_points(self):
        num_lat, num_long = 16, 24
        radius = 165
        for i in range(num_lat + 1):
            lat = math.pi * i / num_lat
            for j in range(num_long):
                lon = 2 * math.pi * j / num_long
                x = radius * math.sin(lat) * math.cos(lon)
                y = radius * math.sin(lat) * math.sin(lon)
                z = radius * math.cos(lat)
                self.sphere_points.append([x, y, z])

    def _get_theme_color(self, r, g, b, a=255):
        """Retorna el color original o un Rojo Alerta si está offline."""
        if self._is_online:
            return QColor(r, g, b, a)
        else:
            # Shift colors to RED spectrum (Critical Alert Mode)
            intensity = (r + g + b) / 765.0
            return QColor(int(240 * intensity + 15), int(10 * intensity), int(30 * intensity), a)

    def _animate(self):
        self._angle_y += self._angle_step
        self._angle_x += self._angle_step * 0.3
        self._pulse_time += 0.02
        self._scan_line_y = (self._scan_line_y + 2) % self.height()
        self._led_angle = (getattr(self, "_led_angle", 0) + 15) % 360
        self.update()

    def _draw_fluorescent_led(self, painter, tx, ty, scale, is_online):
        """Dibuja un LED fluorescente giratorio de alta intensidad."""
        size = 28 * scale
        rect = QRectF(tx - size/2, ty - size/2, size, size)
        center = rect.center()
        
        # 1. Glow Base
        glow = QRadialGradient(center, size * 0.8)
        if is_online:
            glow.setColorAt(0, QColor(0, 255, 255, 200))
            glow.setColorAt(1, Qt.transparent)
            base_col = QColor(0, 255, 255)
        else:
            glow.setColorAt(0, QColor(255, 50, 0, 200))
            glow.setColorAt(1, Qt.transparent)
            base_col = QColor(255, 50, 0)
            
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(rect.adjusted(-5, -5, 5, 5))
        
        # 2. Rotating Segment (Conical)
        rot_grad = QConicalGradient(center, self._led_angle)
        rot_grad.setColorAt(0, base_col)
        rot_grad.setColorAt(0.3, Qt.transparent)
        rot_grad.setColorAt(1, Qt.transparent)
        
        painter.setBrush(rot_grad)
        painter.drawEllipse(rect)
        
        # 3. Inner core
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawEllipse(center, 3 * scale, 3 * scale)

    def _draw_cyber_card(self, painter):
        """Dibuja el contenedor 'Trending' tipo tarjeta de cristal."""
        cw, ch = 820, 580
        cx = (self.width() - cw) // 2
        cy = (self.height() - ch) // 2
        rect = QRectF(cx, cy, cw, ch)
        
        # Shadow Effect
        for i in range(10):
            alpha = int(40 / (i+1))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(rect.adjusted(-i, -i, i, i), 35, 35)

        # Glass Background
        bg_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg_grad.setColorAt(0, QColor(10, 15, 30, 180) if self._is_online else QColor(50, 0, 0, 180))
        bg_grad.setColorAt(1, QColor(5, 5, 10, 240) if self._is_online else QColor(20, 0, 0, 240))
        painter.setBrush(bg_grad)
        painter.setPen(QPen(self._get_theme_color(0, 255, 255, 40), 1))
        painter.drawRoundedRect(rect, 30, 30)
        
        # LED Giratorio en la tarjeta
        self._draw_fluorescent_led(painter, cx + cw - 40, cy + 40, 1.0, self._is_online)

        # HUD Brackets... (Rest of brackets)
        m = 25
        painter.setPen(QPen(self._get_theme_color(0, 255, 255, 180), 2))
        painter.drawLine(cx+m, cy+m, cx+m+30, cy+m)
        painter.drawLine(cx+m, cy+m, cx+m, cy+m+30)
        painter.drawLine(cx+cw-m, cy+m, cx+cw-m-30, cy+m)
        painter.drawLine(cx+cw-m, cy+m, cx+cw-m, cy+m+30)
        painter.drawLine(cx+m, cy+ch-m, cx+m+30, cy+ch-m)
        painter.drawLine(cx+m, cy+ch-m, cx+m, cy+ch-m-30)
        painter.drawLine(cx+cw-m, cy+ch-m, cx+cw-m-30, cy+ch-m)
        painter.drawLine(cx+cw-m, cy+ch-m, cx+cw-m, cy+ch-m-30)

        return cx + cw/2, cy + ch/2, min(cw, ch) / 850.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. DRAW TRENDING CARD
        cx, cy, scale_mult = self._draw_cyber_card(painter)
        scale = scale_mult * 1.1 
        pulse_val = abs(math.sin(self._pulse_time))
        pulse_smooth = (math.sin(self._pulse_time) + 1) / 2
        
        # 2. HEADER
        title_font = QFont("Consolas", int(22 * scale))
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 12 * scale)
        painter.setFont(title_font)
        painter.setPen(self._get_theme_color(255, 255, 255, int(150 + pulse_val * 50)))
        painter.drawText(QRectF(0, cy - 230*scale, self.width(), 60*scale), Qt.AlignCenter, self.vault_name)

        # 3. STATUS INDICATOR
        if not self._is_online:
            painter.setFont(QFont("Consolas", int(10 * scale), QFont.Bold))
            painter.setPen(QColor(255, 50, 0, int(180 + pulse_val * 75)))
            painter.drawText(QRectF(0, cy - 180*scale, self.width(), 20*scale), Qt.AlignCenter, "CRITICAL: SIGNAL LOST - LOCAL ACCESS ONLY")
        else:
            painter.setFont(QFont("Consolas", int(9 * scale)))
            painter.setPen(QColor(0, 255, 255, 100))
            painter.drawText(QRectF(0, cy - 180*scale, self.width(), 20*scale), Qt.AlignCenter, "ENCRYPTED CLOUD SYNC ACTIVE")

        # ... (Rest of sphere drawing)

        # 4. FLOOR VFX
        floor_y = cy + (180 * scale)
        base_glow = QRadialGradient(cx, floor_y, 500 * scale)
        base_glow.setColorAt(0, self._get_theme_color(0, 100, 255, int(40 + 40 * pulse_smooth)))
        base_glow.setColorAt(1, Qt.transparent)
        painter.setBrush(base_glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, floor_y - 150 * scale), 500 * scale, 250 * scale)

        # 5. SPHERE RENDERING
        projected_points = []
        base_scale = (0.95 + (0.25 * pulse_val)) * scale
        for p in self.sphere_points:
            sx, sy, sz = p[0] * base_scale, p[1] * base_scale, p[2] * base_scale
            x = sx * math.cos(self._angle_y) - sz * math.sin(self._angle_y)
            z = sx * math.sin(self._angle_y) + sz * math.cos(self._angle_y)
            y = sy
            ry = y * math.cos(self._angle_x) - z * math.sin(self._angle_x)
            rz = y * math.sin(self._angle_x) + z * math.cos(self._angle_x)
            f_dist = 450 * scale 
            factor = f_dist / (f_dist - rz) if (f_dist - rz) != 0 else 1
            px, py = x * factor + cx, ry * factor + cy
            projected_points.append((px, py, rz))

        num_long = 24
        pen = QPen()
        for i in range(len(projected_points)):
            p1 = projected_points[i]
            p2 = projected_points[(i + 1) % len(projected_points)]
            p3_idx = i + num_long
            p3 = projected_points[p3_idx] if p3_idx < len(projected_points) else None
            alpha = int((140 + (p1[2]/160) * 80) * (0.6 + 0.4 * pulse_val))
            pen.setColor(self._get_theme_color(0, 150, 255, max(40, alpha)))
            pen.setWidthF((1.0 + 1.5 * pulse_val) * scale) 
            painter.setPen(pen)
            max_dist = 75 * base_scale
            if math.hypot(p1[0]-p2[0], p1[1]-p2[1]) < max_dist:
                painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
            if p3 and math.hypot(p1[0]-p3[0], p1[1]-p3[1]) < max_dist:
                painter.drawLine(int(p1[0]), int(p1[1]), int(p3[0]), int(p3[1]))

        # Front Glow Points
        for p in projected_points:
            if p[2] > 0: 
                p_alpha = int(255 * (p[2]/160) * pulse_val)
                painter.setBrush(self._get_theme_color(0, 255, 255, max(0, p_alpha)))
                size = (2.0 + 2.5 * pulse_val) * scale
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(p[0], p[1]), size, size)

        # 6. FOOTER: Instructions
        instr_font = QFont("Consolas", int(10 * scale))
        instr_font.setLetterSpacing(QFont.AbsoluteSpacing, 4 * scale)
        painter.setFont(instr_font)
        painter.setPen(self._get_theme_color(255, 255, 255, int(100 + 100 * pulse_val)))
        painter.drawText(QRectF(0, cy + 220*scale, self.width(), 40*scale), Qt.AlignCenter, "PRESS [ ENTER ] TO UNLOCK SYSTEM")

        app_font = QFont("Segoe UI", int(16 * scale), QFont.Bold)
        app_font.setLetterSpacing(QFont.AbsoluteSpacing, 3 * scale)
        painter.setFont(app_font)
        painter.setPen(self._get_theme_color(0, 255, 255, 140))
        margin = 35 * scale
        painter.drawText(QRectF(margin, self.height() - margin - 35*scale, 400*scale, 35*scale), Qt.AlignLeft | Qt.AlignVCenter, self.vault_name)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.unlocked.emit()
            self.close()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.unlocked.emit()
            self.close()
            event.accept()
