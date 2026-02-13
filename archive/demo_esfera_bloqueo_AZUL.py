import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient, QFont

class NeonSphereLock(QWidget):
    """
    Concepto de Pantalla de Bloqueo 'PassGuardian':
    Una esfera 3D holográfica de neón que gira en un espacio oscuro.
    Representa la protección total del sistema.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassGuardian - Security Core")
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #020617;") # Slate 950 (Oscuro profundo)
        
        self._angle_x = 0
        self._angle_y = 0
        self._angle_step = 0.008
        self._pulse_time = 0 # Inicializado aquí para persistencia
        
        # Puntos de la esfera (Mayor densidad)
        self.points = []
        self._generate_sphere_points()
        
        # Animación
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.setInterval(20) # 50 FPS estables
        self.timer.start()
        
        # Texto de estado
        self.status_label = QLabel("SECURE CORE ACTIVE", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #10b981; 
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 6px;
        """)
        self.status_label.setGeometry(0, 520, 800, 50)

    def _generate_sphere_points(self):
        """Genera puntos que forman una red esférica más densa"""
        num_lat = 16  # Mas latitud
        num_long = 24 # Mas longitud para mas "rayas"
        radius = 160
        
        for i in range(num_lat + 1):
            lat = math.pi * i / num_lat
            for j in range(num_long):
                lon = 2 * math.pi * j / num_long
                
                x = radius * math.sin(lat) * math.cos(lon)
                y = radius * math.sin(lat) * math.sin(lon)
                z = radius * math.cos(lat)
                self.points.append([x, y, z])

    def _update_animation(self):
        self._angle_y += self._angle_step
        self._angle_x += self._angle_step * 0.3 # Diferente velocidad para efecto 3D
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2 - 20
        
        # Color Principal: AZUL ELÉCTRICO (Cyber Blue)
        # Reemplazamos QColor(16, 185, 129) por QColor(59, 130, 246)
        main_color = QColor(59, 130, 246)
        
        # 1. Pulso INTENSO (como antes) pero LENTO
        self._pulse_time += 0.02 
        pulse = abs(math.sin(self._pulse_time)) 
        
        # Factor de escala pulsante MARCADO (30% de amplitud)
        scale_factor = 0.9 + (0.3 * pulse)
        
        # 2. Resplandor pulsante INTENSO (AZUL)
        glow_radius = 200 + (100 * pulse)
        glow_alpha = int(20 + 60 * pulse)
        glow = QRadialGradient(center_x, center_y, glow_radius)
        glow.setColorAt(0, QColor(main_color.red(), main_color.green(), main_color.blue(), glow_alpha))
        glow.setColorAt(1, Qt.transparent)
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - glow_radius), int(center_y - glow_radius), 
                            int(glow_radius * 2), int(glow_radius * 2))
        
        # 3. Proyectar y aplicar escala pulsante
        projected_points = []
        for p in self.points:
            sx = p[0] * scale_factor
            sy = p[1] * scale_factor
            sz = p[2] * scale_factor
            
            x = sx * math.cos(self._angle_y) - sz * math.sin(self._angle_y)
            z = sx * math.sin(self._angle_y) + sz * math.cos(self._angle_y)
            y = sy
            
            new_y = y * math.cos(self._angle_x) - z * math.sin(self._angle_x)
            new_z = y * math.sin(self._angle_x) + z * math.cos(self._angle_x)
            
            factor = 450 / (450 - new_z)
            px = x * factor + center_x
            py = new_y * factor + center_y
            projected_points.append((px, py, new_z))

        # 4. Dibujar RED con brillo variable MARCADO (AZUL INTENSO)
        num_long = 24
        pen = QPen()
        for i in range(len(projected_points)):
            p1 = projected_points[i]
            p2 = projected_points[(i + 1) % len(projected_points)]
            p3_idx = i + num_long
            p3 = projected_points[p3_idx] if p3_idx < len(projected_points) else None

            # Opacidad que cambia MUCHO con el pulso (INTENSO)
            alpha = int((100 + (p1[2]/160) * 80) * (0.4 + 0.6 * pulse))
            pen.setColor(QColor(main_color.red(), main_color.green(), main_color.blue(), max(10, alpha)))
            pen.setWidthF(0.5 + 1.0 * pulse) 
            painter.setPen(pen)
            
            d12 = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
            if d12 < 70 * scale_factor:
                painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
                
            if p3:
                d13 = math.sqrt((p1[0]-p3[0])**2 + (p1[1]-p3[1])**2)
                if d13 < 70 * scale_factor:
                    painter.drawLine(int(p1[0]), int(p1[1]), int(p3[0]), int(p3[1]))

        # 5. Puntos brillantes que crecen claramente (AZUL)
        painter.setPen(Qt.NoPen)
        for p in projected_points:
            if p[2] > 0: 
                p_alpha = int(255 * (p[2]/160) * pulse)
                painter.setBrush(QColor(main_color.red(), main_color.green(), main_color.blue(), max(0, p_alpha)))
                size = (1.5 + 2.5 * pulse) 
                painter.drawEllipse(QPointF(p[0], p[1]), size, size)

        # 6. Partículas de seguridad (AZUL)
        painter.setPen(QColor(main_color.red(), main_color.green(), main_color.blue(), 100))
        for _ in range(5): # Menos partículas para que el azul destaque
            rx = random.randint(0, self.width())
            ry = random.randint(0, self.height())
            painter.drawPoint(rx, ry)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeonSphereLock()
    window.show()
    sys.exit(app.exec_())
