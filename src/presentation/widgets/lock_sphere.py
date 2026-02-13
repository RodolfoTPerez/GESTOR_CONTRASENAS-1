import math
import random
import urllib.request
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QPainterPath, QFont, QPolygonF, QLinearGradient, QConicalGradient

from src.infrastructure.database.db_manager import DBManager
from src.infrastructure.repositories.secret_repo import SecretRepository
from src.domain.services.session_service import SessionService

class HyperRealVaultCore(QWidget):
    """
    RÉPLICA INTEGRADA: Suelo de Bóveda Hiperrealista + Esfera de Neón Intensa.
    Pantalla de Bloqueo de Seguridad para PassGuardian.
    """
    unlocked = pyqtSignal() # Señal para capturar el regreso al login
    
    def __init__(self, vault_name="VULTRAX CORE"):
        super().__init__()
        self.setWindowTitle("SECURITY LOCK")
        
        # Ventana Flotante de Seguridad (No Kiosco)
        self.resize(1000, 650)
        self._center_on_screen()
        
        self.setStyleSheet("background-color: #00020A;")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        self.vault_name = str(vault_name).upper()
        self._angle_x = 0
        self._angle_y = 0
        self._angle_step = 0.008
        self._pulse_time = 0
        
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
        """
        Obtiene el nombre oficial desde el cache local (meta).
        """
        try:
            db = DBManager("vultrax")
            # El nombre suele estar en una tabla de metadatos o similar. 
            # Como HyperRealVaultCore es un widget visual, intentamos leer de la DB directamente si es posible
            # o fallar silenciosamente al nombre por defecto.
            cursor = db.execute("SELECT value FROM meta WHERE key = 'instance_name'")
            row = cursor.fetchone()
            if row:
                self.vault_name = row[0].upper()
        except Exception:
            pass

    def _check_connectivity(self):
        """Verifica si hay acceso a la red de forma no bloqueante."""
        try:
            urllib.request.urlopen('https://www.google.com', timeout=2)
            self._is_online = True
        except:
            self._is_online = False

    def _generate_sphere_points(self):
        """Genera puntos para la red esférica densa"""
        num_lat = 16
        num_long = 24
        radius = 160
        for i in range(num_lat + 1):
            lat = math.pi * i / num_lat
            for j in range(num_long):
                lon = 2 * math.pi * j / num_long
                x = radius * math.sin(lat) * math.cos(lon)
                y = radius * math.sin(lat) * math.sin(lon)
                z = radius * math.cos(lat)
                self.sphere_points.append([x, y, z])

    def _get_color(self, r, g, b, a=255):
        """Retorna el color original o su versión roja si está offline."""
        if self._is_online:
            return QColor(r, g, b, a)
        else:
            intensity = (r + g + b) / 765.0
            return QColor(int(225 * intensity + 30), int(29 * intensity), int(72 * intensity), a)

    def _animate(self):
        self._angle_y += self._angle_step
        self._angle_x += self._angle_step * 0.3
        self._pulse_time += 0.02
        self.update()

    def _draw_hyper_floor(self, painter, cx, cy, pulse):
        """Dibuja el suelo de bóveda con pulso sincronizado"""
        base_dim = min(self.width(), self.height())
        scale = (base_dim / 850.0) * 0.8
        floor_y = cy + (200 * scale) 
        
        base_glow = QRadialGradient(cx, floor_y, 600 * scale)
        base_alpha = int(30 + 50 * pulse)
        base_glow.setColorAt(0, self._get_color(0, 100, 255, base_alpha))
        base_glow.setColorAt(1, Qt.transparent)
        painter.setBrush(base_glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, floor_y - 200 * scale), 600 * scale, 300 * scale)

        layers = [
            [550, 1.0, QColor(0, 100, 255, 80), 0.1, Qt.SolidLine, False],
            [520, 1.5, QColor(0, 150, 255, 120), 0.2, Qt.SolidLine, True],
            [500, 1.0, QColor(0, 80, 255, 90), -0.2, Qt.DotLine, False],
            [480, 6.0, QColor(0, 80, 255, 150), -0.4, Qt.SolidLine, False],
            [450, 1.0, QColor(59, 130, 246, 110), 0.3, Qt.DashLine, False],
            [420, 2.0, QColor(59, 130, 246, 210), 0.6, Qt.DashLine, True],
            [390, 1.0, QColor(0, 255, 255, 120), -0.3, Qt.SolidLine, False],
            [350, 4.0, QColor(0, 255, 255, 255), 0.3, Qt.SolidLine, False],
            [320, 1.0, QColor(0, 180, 255, 110), 0.15, Qt.DotLine, False],
            [280, 1.5, QColor(0, 100, 255, 160), -0.1, Qt.DotLine, False],
            [240, 1.0, QColor(0, 200, 255, 140), 0.5, Qt.DashLine, False],
            [200, 8.0, QColor(0, 255, 255, 255), 0.8, Qt.CustomDashLine, False],
        ]

        for r_base, w, col, speed, style, ticks in layers:
            r = r_base * scale
            rect = QRectF(cx - r, floor_y - r/4, r * 2, r/2)
            rot = self._angle_y * 100 * speed
            pulse_mult = 0.6 + 0.4 * pulse
            curr_alpha = int(col.alpha() * pulse_mult)
            curr_col = self._get_color(col.red(), col.green(), col.blue(), curr_alpha)

            pen = QPen(curr_col, w * scale)
            if style == Qt.CustomDashLine: pen.setDashPattern([2, 5])
            else: pen.setStyle(style)
            painter.setPen(pen)
            painter.drawEllipse(rect)
            
            if ticks:
                painter.setPen(QPen(QColor(col.red(), col.green(), col.blue(), curr_alpha), 1))
                for t in range(72):
                    angle = t * (360/72) + (rot * 0.5)
                    if (angle % 360) < 180:
                        painter.drawArc(rect, int(angle * 16), 16)
            
            scan_grad = QConicalGradient(cx, floor_y, rot * 2)
            scan_grad.setColorAt(0, Qt.transparent)
            scan_grad.setColorAt(0.1, self._get_color(255, 255, 255, int(220 * pulse)))
            scan_grad.setColorAt(0.2, Qt.transparent)
            painter.setPen(QPen(scan_grad, w + 1))
            painter.drawEllipse(rect)

    def _draw_status_shield(self, painter, cx, cy, scale):
        margin = 40 * scale
        sw, sh = 60 * scale, 75 * scale
        tx = self.width() - sw/2 - margin
        ty = margin + sh/2
        
        if self._is_online:
            base_col = QColor(57, 255, 20, 100)
            border_col = QColor(57, 255, 20, 200)
            glow_col = QColor(57, 255, 20, 40)
        else:
            flicker = 150 if random.random() > 0.9 else 40
            base_col = QColor(255, 50, 50, flicker)
            border_col = QColor(255, 50, 50, 180)
            glow_col = QColor(255, 50, 50, 30)

        glow = QRadialGradient(tx, ty, sw)
        glow.setColorAt(0, glow_col)
        glow.setColorAt(1, Qt.transparent)
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(tx, ty), sw, sw)

        def get_shield_path(w, h):
            path = QPainterPath()
            path.moveTo(tx, ty - h/2)
            path.lineTo(tx + w/2, ty - h/3)
            path.lineTo(tx + w/2, ty + h/6)
            path.quadTo(tx + w/2, ty + h/2, tx, ty + h*0.6)
            path.quadTo(tx - w/2, ty + h/2, tx - w/2, ty + h/6)
            path.lineTo(tx - w/2, ty - h/3)
            path.closeSubpath()
            return path

        outer_path = get_shield_path(sw, sh)
        painter.setPen(QPen(border_col, 3 * scale))
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.drawPath(outer_path)

        inner_path = get_shield_path(sw * 0.7, sh * 0.7)
        painter.setPen(QPen(border_col, 1 * scale))
        inner_fill = QLinearGradient(tx, ty - sh/2, tx, ty + sh/2)
        inner_fill.setColorAt(0, base_col)
        inner_fill.setColorAt(1, QColor(base_col.red(), base_col.green(), base_col.blue(), 20))
        painter.setBrush(inner_fill)
        painter.drawPath(inner_path)

        def draw_nut(nx, ny, nsize):
            nut_path = QPainterPath()
            for i in range(6):
                angle = math.radians(i * 60)
                px = nx + nsize * math.cos(angle)
                py = ny + nsize * math.sin(angle)
                if i == 0: nut_path.moveTo(px, py)
                else: nut_path.lineTo(px, py)
            nut_path.closeSubpath()
            painter.setPen(QPen(border_col, 1.5 * scale))
            painter.setBrush(QColor(20, 20, 25, 230))
            painter.drawPath(nut_path)
            painter.setBrush(QColor(base_col.red(), base_col.green(), base_col.blue(), 100))
            painter.drawEllipse(QPointF(nx, ny), nsize * 0.4, nsize * 0.4)

        nut_dist_x, nut_dist_y = sw * 0.4, sh * 0.3
        nut_size = 5 * scale
        draw_nut(tx - nut_dist_x, ty - nut_dist_y, nut_size)
        draw_nut(tx + nut_dist_x, ty - nut_dist_y, nut_size)
        draw_nut(tx, ty + sh * 0.4, nut_size)

        sym_pen = QPen(border_col, 2 * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(sym_pen)
        if self._is_online:
            cx1, cy1 = tx - 5*scale, ty
            painter.drawLine(QPointF(cx1, cy1), QPointF(tx, ty + 5*scale))
            painter.drawLine(QPointF(tx, ty + 5*scale), QPointF(tx + 8*scale, ty - 5*scale))
        else:
            painter.drawLine(QPointF(tx-5*scale, ty-5*scale), QPointF(tx+5*scale, ty+5*scale))
            painter.drawLine(QPointF(tx+5*scale, ty-5*scale), QPointF(tx-5*scale, ty+5*scale))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, (self.height() / 2) - 40 
        base_dim = min(self.width(), self.height())
        scale = (base_dim / 850.0) * 0.8
        pulse_val = abs(math.sin(self._pulse_time))
        pulse_smooth = (math.sin(self._pulse_time) + 1) / 2
        
        title_font = QFont("Segoe UI", int(24 * scale), QFont.Bold)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 10 * scale)
        painter.setFont(title_font)
        painter.setPen(self._get_color(0, 255, 255, int(180 + 75 * pulse_val)))
        painter.drawText(QRectF(0, 30 * scale, self.width(), 50 * scale), Qt.AlignCenter, self.vault_name)

        self._draw_hyper_floor(painter, cx, cy, pulse_smooth)
        self._draw_status_shield(painter, cx, cy, scale)
        
        base_scale = (0.9 + (0.3 * pulse_val)) * scale
        projected_points = []
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
            alpha = int((130 + (p1[2]/160) * 100) * (0.5 + 0.5 * pulse_val))
            pen.setColor(self._get_color(0, 120, 255, max(30, alpha)))
            pen.setWidthF((0.8 + 1.2 * pulse_val) * scale) 
            painter.setPen(pen)
            max_dist = 70 * base_scale
            d12 = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
            if d12 < max_dist: painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
            if p3:
                d13 = math.sqrt((p1[0]-p3[0])**2 + (p1[1]-p3[1])**2)
                if d13 < max_dist: painter.drawLine(int(p1[0]), int(p1[1]), int(p3[0]), int(p3[1]))

        painter.setPen(Qt.NoPen)
        for p in projected_points:
            if p[2] > 0: 
                p_alpha = int(255 * (p[2]/160) * pulse_val)
                painter.setBrush(self._get_color(0, 255, 255, max(0, p_alpha)))
                size = (1.8 + 2.8 * pulse_val) * scale
                painter.drawEllipse(QPointF(p[0], p[1]), size, size)

        instr_font = QFont("Segoe UI", int(11 * scale))
        instr_font.setLetterSpacing(QFont.AbsoluteSpacing, 3 * scale)
        painter.setFont(instr_font)
        painter.setPen(self._get_color(0, 255, 255, int(100 + 100 * pulse_val)))
        bottom_area = QRectF(0, self.height() * 0.90, self.width(), self.height() * 0.10)
        painter.drawText(bottom_area, Qt.AlignCenter, "PRESS [ ENTER ] TO UNLOCK SYSTEM")

        app_font = QFont("Segoe UI", int(16 * scale), QFont.Bold)
        app_font.setLetterSpacing(QFont.AbsoluteSpacing, 3 * scale)
        painter.setFont(app_font)
        painter.setPen(self._get_color(0, 255, 255, 140))
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
