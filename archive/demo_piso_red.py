import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient

class NetworkFloor(QWidget):
    """
    Concepto de Suelo de Red Interconectada (Mesh Floor)
    Basado en la imagen: Nodos azules conectados por líneas en perspectiva.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassGuardian - Network Floor Concept")
        self.setFixedSize(1200, 600)
        self.setStyleSheet("background-color: #010208;")
        
        # Parámetros de la red
        self.cols = 20
        self.rows = 15
        self.spacing_x = 80
        self.spacing_z = 60
        
        # Generar puntos con ligera irregularidad
        self.points = []
        for r in range(self.rows):
            row_points = []
            for c in range(self.cols):
                # x, y (altura), z (profundidad)
                x = (c - self.cols/2) * self.spacing_x
                y = 0 
                z = r * self.spacing_z
                # Añadir ruido para que no sea una rejilla perfecta
                x += random.uniform(-15, 15)
                z += random.uniform(-10, 10)
                row_points.append([x, y, z, random.uniform(0, math.pi * 2)]) # last is phase
            self.points.append(row_points)
            
        self._time = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.setInterval(30)
        self.timer.start()

    def _animate(self):
        self._time += 0.05
        # Mover los puntos ligeramente (efecto onda)
        for r in range(self.rows):
            for c in range(self.cols):
                # Oscilación suave en Y
                self.points[r][c][1] = math.sin(self._time + self.points[r][c][3]) * 5
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = self.width() / 2
        cy = self.height() / 2 + 100 # Bajar el horizonte
        
        # Color azul de la imagen
        blue_line = QColor(0, 120, 255, 180)
        blue_node = QColor(0, 200, 255, 255)
        
        # Proyectar puntos a 2D
        projected = []
        for r in range(self.rows):
            row_projected = []
            for c in range(self.cols):
                p = self.points[r][c]
                
                # Proyección simple de perspectiva
                # fov / (fov + z)
                view_dist = 400
                factor = view_dist / (view_dist + p[2])
                
                px = p[0] * factor + cx
                py = p[1] * factor + cy + (p[2] * 0.5) # Desplazamiento hacia abajo según profundidad
                
                row_projected.append((px, py, factor))
            projected.append(row_projected)

        # Dibujar líneas (Conexiones)
        for r in range(self.rows):
            for c in range(self.cols):
                p1 = projected[r][c]
                
                # Conectar con el vecino a la derecha
                if c < self.cols - 1:
                    p2 = projected[r][c+1]
                    alpha = int(255 * p1[2]) # Más transparente al fondo
                    painter.setPen(QPen(QColor(0, 100, 255, alpha), 1))
                    painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
                
                # Conectar con el vecino de abajo
                if r < self.rows - 1:
                    p2 = projected[r+1][c]
                    alpha = int(255 * p1[2])
                    painter.setPen(QPen(QColor(0, 100, 255, alpha), 1))
                    painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))

        # Dibujar Nodos (Puntos)
        for r in range(self.rows):
            for c in range(self.cols):
                p = projected[r][c]
                alpha = int(255 * p[2])
                size = 3 * p[2] # Más pequeños al fondo
                
                painter.setPen(Qt.NoPen)
                # Nodo principal
                painter.setBrush(QColor(0, 200, 255, alpha))
                painter.drawEllipse(QPointF(p[0], p[1]), size, size)
                
                # Glow del nodo
                painter.setBrush(QColor(0, 150, 255, int(alpha * 0.4)))
                painter.drawEllipse(QPointF(p[0], p[1]), size*2, size*2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkFloor()
    window.show()
    sys.exit(app.exec_())
