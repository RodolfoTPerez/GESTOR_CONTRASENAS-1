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
        self._angle_step = 0.008  # Giro mucho mas lento y elegante
        
        # Puntos de la esfera (Mayor densidad para que se vea mas completa)
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
        
        # 1. Resplandor pulsante
        pulse = (math.sin(self._angle_y * 4) + 1) / 2
        glow_radius = 230 + (20 * pulse)
        glow = QRadialGradient(center_x, center_y, glow_radius)
        glow.setColorAt(0, QColor(16, 185, 129, int(40 + 10 * pulse)))
        glow.setColorAt(1, Qt.transparent)
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - glow_radius), int(center_y - glow_radius), 
                            int(glow_radius * 2), int(glow_radius * 2))
        
        # 2. Proyectar y dibujar
        projected_points = []
        for p in self.points:
            # Rotación Y
            x = p[0] * math.cos(self._angle_y) - p[2] * math.sin(self._angle_y)
            z = p[0] * math.sin(self._angle_y) + p[2] * math.cos(self._angle_y)
            y = p[1]
            
            # Rotación X
            new_y = y * math.cos(self._angle_x) - z * math.sin(self._angle_x)
            new_z = y * math.sin(self._angle_x) + z * math.cos(self._angle_x)
            
            factor = 450 / (450 - new_z)
            px = x * factor + center_x
            py = new_y * factor + center_y
            projected_points.append((px, py, new_z))

        # 3. Dibujar RED de lineas (Aumentado para que parezca una rejilla)
        # Dibujamos conexiones longitudinales y latitudinales
        num_long = 24
        pen = QPen()
        for i in range(len(projected_points)):
            p1 = projected_points[i]
            
            # Conexión con el siguiente punto (Longitud)
            p2 = projected_points[(i + 1) % len(projected_points)]
            
            # Conexión con el punto de abajo (Latitud)
            p3_idx = i + num_long
            p3 = projected_points[p3_idx] if p3_idx < len(projected_points) else None

            # Color segun profundidad
            alpha = int(100 + (p1[2]/160) * 80)
            pen.setColor(QColor(16, 185, 129, max(10, alpha)))
            
            # Dibujar lineas de la rejilla
            painter.setPen(pen)
            
            # Dibujar si la distancia es coherente (evitar saltos de proyeccion)
            d12 = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
            if d12 < 50:
                painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
                
            if p3:
                d13 = math.sqrt((p1[0]-p3[0])**2 + (p1[1]-p3[1])**2)
                if d13 < 50:
                    painter.drawLine(int(p1[0]), int(p1[1]), int(p3[0]), int(p3[1]))

        # 4. Puntos brillantes en intersecciones frontales
        painter.setPen(Qt.NoPen)
        for p in projected_points:
            if p[2] > 60: # Solo los de adelante
                alpha = int((p[2]/160) * 255)
                painter.setBrush(QColor(16, 185, 129, alpha))
                painter.drawEllipse(QPointF(p[0], p[1]), 1.5, 1.5)

        # Efecto de partículas de seguridad aleatorias
        painter.setPen(QColor(16, 185, 129, 100))
        for _ in range(10):
            rx = random.randint(0, self.width())
            ry = random.randint(0, self.height())
            painter.drawPoint(rx, ry)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeonSphereLock()
    window.show()
    sys.exit(app.exec_())
