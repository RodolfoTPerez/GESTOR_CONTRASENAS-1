import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QPainterPath, QFont, QPolygonF, QLinearGradient, QConicalGradient

class HyperRealVaultCore(QWidget):
    """
    RÉPLICA INTEGRADA: Suelo de Bóveda Hiperrealista + Esfera de Neón Intensa.
    Estética Ghost Gray para el suelo y Azul Eléctrico para la esfera.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PASSGUARDIAN - INTEGRATED SECURITY CORE")
        self.setFixedSize(1100, 910)
        self.setStyleSheet("background-color: #00020A;")
        
        self._angle_x = 0
        self._angle_y = 0
        self._angle_step = 0.008
        self._pulse_time = 0
        
        # Puntos de la esfera (Cargados del código de neón)
        self.sphere_points = []
        self._generate_sphere_points()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.setInterval(20)
        self.timer.start()

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

    def _animate(self):
        self._angle_y += self._angle_step
        self._angle_x += self._angle_step * 0.3
        self._pulse_time += 0.02
        self.update()

    def _draw_hyper_floor(self, painter, cx, cy, pulse):
        """Dibuja el suelo de bóveda con estética Glassmorphism Azul Intenso y Densidad Alta"""
        
        # 1. Resplandor base de profundidad (Glow azul eléctrico intenso)
        base_glow = QRadialGradient(cx, cy + 220, 600)
        base_glow.setColorAt(0, QColor(0, 100, 255, 70))
        base_glow.setColorAt(1, Qt.transparent)
        painter.setBrush(base_glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - 600), int(cy - 100), 1200, 600)

        # 2. Capas de la bóveda (12 anillos con Azul Intenso y Glassmorphism)
        layers = [
            [550, 1.0, QColor(0, 100, 255, 80), 0.1, Qt.SolidLine, False],
            [520, 1.5, QColor(0, 150, 255, 100), 0.2, Qt.SolidLine, True],
            [500, 1.0, QColor(0, 80, 255, 90), -0.2, Qt.DotLine, False],
            [480, 6.0, QColor(0, 80, 255, 120), -0.4, Qt.SolidLine, False],
            [450, 1.0, QColor(59, 130, 246, 100), 0.3, Qt.DashLine, False],
            [420, 2.0, QColor(59, 130, 246, 180), 0.6, Qt.DashLine, True],
            [390, 1.0, QColor(0, 255, 255, 100), -0.3, Qt.SolidLine, False],
            [350, 4.0, QColor(0, 255, 255, 200), 0.3, Qt.SolidLine, False],
            [320, 1.0, QColor(0, 180, 255, 110), 0.15, Qt.DotLine, False],
            [280, 1.5, QColor(0, 100, 255, 150), -0.1, Qt.DotLine, False],
            [240, 1.0, QColor(0, 200, 255, 130), 0.5, Qt.DashLine, False],
            [200, 8.0, QColor(0, 255, 255, 230), 0.8, Qt.CustomDashLine, False],
        ]

        for r, w, col, speed, style, ticks in layers:
            rect = QRectF(cx - r, cy + 220 - r/4, r * 2, r/2)
            rot = self._angle_y * 100 * speed
            
            # Anillo principal (Transparencia extrema)
            pen = QPen(col, w)
            if style == Qt.CustomDashLine: pen.setDashPattern([2, 5])
            else: pen.setStyle(style)
            painter.setPen(pen)
            painter.drawEllipse(rect)
            
            # Engranajes mínimos
            if w > 1:
                painter.setPen(QPen(QColor(col.red(), col.green(), col.blue(), 60), w))
                for t in range(12):
                    angle = (t * (360/12) + rot)
                    painter.drawArc(rect, int(angle * 16), 10 * 16)

            if ticks:
                painter.setPen(QPen(QColor(col.red(), col.green(), col.blue(), 50), 0.5))
                for t in range(72):
                    angle = t * (360/72) + (rot * 0.5)
                    if (angle % 360) < 180:
                        painter.drawArc(rect, int(angle * 16), 8)
            
            # Escaneo Radial (Solo un destello fugaz)
            scan_grad = QConicalGradient(cx, cy + 220, rot * 2)
            scan_grad.setColorAt(0, Qt.transparent)
            scan_grad.setColorAt(0.1, QColor(255, 255, 255, int(60 * pulse)))
            scan_grad.setColorAt(0.2, Qt.transparent)
            painter.setPen(QPen(scan_grad, w))
            painter.drawEllipse(rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx, cy = self.width() / 2, self.height() / 2 - 80
        pulse_val = abs(math.sin(self._pulse_time))
        pulse_smooth = (math.sin(self._pulse_time) + 1) / 2
        
        # --- 1. SUELO HIPERREALISTA ---
        self._draw_hyper_floor(painter, cx, cy, pulse_smooth)
        
        # --- 2. DIBUJAR ESFERA DE NEÓN (Código de Neón Azul) ---
        main_color = QColor(59, 130, 246)
        scale_factor = 0.9 + (0.3 * pulse_val)
        
        # Glow Atmosférico
        glow_radius = 200 + (100 * pulse_val)
        glow_alpha = int(20 + 60 * pulse_val)
        glow = QRadialGradient(cx, cy, glow_radius)
        glow.setColorAt(0, QColor(main_color.red(), main_color.green(), main_color.blue(), glow_alpha))
        glow.setColorAt(1, Qt.transparent)
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - glow_radius), int(cy - glow_radius), int(glow_radius * 2), int(glow_radius * 2))
        
        # Proyectar puntos de la esfera
        projected_points = []
        for p in self.sphere_points:
            sx, sy, sz = p[0] * scale_factor, p[1] * scale_factor, p[2] * scale_factor
            
            # Rotación
            x = sx * math.cos(self._angle_y) - sz * math.sin(self._angle_y)
            z = sx * math.sin(self._angle_y) + sz * math.cos(self._angle_y)
            y = sy
            ry = y * math.cos(self._angle_x) - z * math.sin(self._angle_x)
            rz = y * math.sin(self._angle_x) + z * math.cos(self._angle_x)
            
            factor = 450 / (450 - rz)
            px, py = x * factor + cx, ry * factor + cy
            projected_points.append((px, py, rz))

        # Dibujar Red (Malla) de la esfera
        num_long = 24
        pen = QPen()
        for i in range(len(projected_points)):
            p1 = projected_points[i]
            p2 = projected_points[(i + 1) % len(projected_points)]
            p3_idx = i + num_long
            p3 = projected_points[p3_idx] if p3_idx < len(projected_points) else None

            alpha = int((100 + (p1[2]/160) * 80) * (0.4 + 0.6 * pulse_val))
            pen.setColor(QColor(main_color.red(), main_color.green(), main_color.blue(), max(10, alpha)))
            pen.setWidthF(0.5 + 1.0 * pulse_val) 
            painter.setPen(pen)
            
            d12 = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
            if d12 < 70 * scale_factor:
                painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
            if p3:
                d13 = math.sqrt((p1[0]-p3[0])**2 + (p1[1]-p3[1])**2)
                if d13 < 70 * scale_factor:
                    painter.drawLine(int(p1[0]), int(p1[1]), int(p3[0]), int(p3[1]))

        # Dibujar Puntos y Partículas
        painter.setPen(Qt.NoPen)
        for p in projected_points:
            if p[2] > 0: 
                p_alpha = int(255 * (p[2]/160) * pulse_val)
                painter.setBrush(QColor(main_color.red(), main_color.green(), main_color.blue(), max(0, p_alpha)))
                size = (1.5 + 2.5 * pulse_val) 
                painter.drawEllipse(QPointF(p[0], p[1]), size, size)

        # Partículas aleatorias
        painter.setPen(QPen(QColor(main_color.red(), main_color.green(), main_color.blue(), 100), 1))
        for _ in range(5):
            painter.drawPoint(random.randint(0, self.width()), random.randint(0, self.height()))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HyperRealVaultCore()
    window.show()
    sys.exit(app.exec_())
