import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QPainterPath, QFont, QPolygonF, QLinearGradient, QConicalGradient

class HyperRealVaultCore(QWidget):
    """
    RÉPLICA HIPERREALISTA - PASSGUARDIAN VAULT CORE
    Foco: Suelo de Bóveda Mecánica/Digital con profundidad, texturas y engranajes.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PASSGUARDIAN CRYPTO-VAULT CORE")
        self.setFixedSize(1100, 900)
        self.setStyleSheet("background-color: #00020A;")
        
        self._angle_y = 0
        self._pulse_time = 0
        
        # Componentes internos de la esfera
        self.internal_chips = []
        for _ in range(20):
            self.internal_chips.append({
                'pos': [random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(-100, 100)],
                'size': [random.uniform(25, 60), random.uniform(12, 25)],
                'color': QColor(0, 255, 255, 140)
            })

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.setInterval(16)
        self.timer.start()

    def _animate(self):
        self._angle_y += 0.005
        self._pulse_time += 0.02
        self.update()

    def _draw_hyper_floor(self, painter, cx, cy, pulse):
        """Dibuja el suelo de bóveda hiperrealista con profundidad y detalle mecánico"""
        
        # 1. Brillo de profundidad base (Ambient Occlusion)
        base_glow = QRadialGradient(cx, cy + 200, 600)
        base_glow.setColorAt(0, QColor(0, 40, 100, 50))
        base_glow.setColorAt(1, Qt.transparent)
        painter.setBrush(base_glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - 600), int(cy - 100), 1200, 600)

        # 2. Anillos de Bóveda Hiperrealistas
        # Definición de capas: [radio, grosor, color, velocidad, dash, tiene_ticks]
        layers = [
            [520, 1.5, QColor(0, 80, 200, 40), 0.2, Qt.SolidLine, True],   # Anillo Exterior Guía
            [480, 8, QColor(0, 120, 255, 80), -0.4, Qt.SolidLine, False], # Anillo de Bloqueo Pesado
            [420, 2, QColor(0, 200, 255, 100), 0.6, Qt.DashLine, True],   # Escala Numérica
            [350, 4, QColor(0, 255, 255, 150), 0.3, Qt.SolidLine, False], # Anillo de Datos Activo
            [280, 1, QColor(0, 100, 255, 60), -0.1, Qt.DotLine, False],   # Anillo de Soporte Interno
        ]

        for i, (r, w, col, speed, style, ticks) in enumerate(layers):
            # Proyeccion de perspectiva (Elipse aplastada)
            rect = QRectF(cx - r, cy + 220 - r/4, r * 2, r/2)
            rot = self._angle_y * 100 * speed
            
            # Dibujar sombra proyectada del anillo
            painter.setPen(QPen(QColor(0, 0, 0, 100), w + 2))
            painter.drawEllipse(rect)
            
            # Dibujar el cuerpo del anillo
            pen = QPen(col, w)
            pen.setStyle(style)
            painter.setPen(pen)
            painter.drawEllipse(rect)
            
            # Añadir 'Dientes' o Engranajes de Bóveda
            if w > 3:
                painter.setPen(QPen(col, w + 2))
                num_teeth = 12
                for t in range(num_teeth):
                    angle = (t * (360/num_teeth) + rot)
                    painter.drawArc(rect, int(angle * 16), 10 * 16)

            # Añadir Ticks de Precisión e Ingeniería
            if ticks:
                num_ticks = 72
                painter.setPen(QPen(QColor(col.red(), col.green(), col.blue(), 100), 1))
                for t in range(num_ticks):
                    angle = t * (360/num_ticks) + (rot * 0.5)
                    # Solo dibujar si está en el frente de la perspectiva para realismo
                    if (angle % 360) < 180:
                        painter.drawArc(rect, int(angle * 16), 16) # Tiny tick
            
            # Efecto de Escaneo Radial (Brillo que recorre el anillo)
            scan_grad = QConicalGradient(cx, cy + 220, rot * 2)
            scan_grad.setColorAt(0, Qt.transparent)
            scan_grad.setColorAt(0.1, QColor(255, 255, 255, int(150 * pulse)))
            scan_grad.setColorAt(0.2, Qt.transparent)
            painter.setPen(QPen(scan_grad, w + 1))
            painter.drawEllipse(rect)

    def _draw_processor(self, painter, cx, cy, pulse):
        """Dibuja el microprocesador con pins detallados y zócalo 3D"""
        cyan = QColor(0, 255, 255)
        
        # 1. Zócalo (Socket) inferior con profundidad
        socket_path = self._create_rhombus(cx, cy + 245, 260, 140)
        painter.setPen(QPen(QColor(0, 100, 255, 120), 2))
        painter.setBrush(QColor(2, 8, 25))
        painter.drawPath(socket_path)
        
        # 2. Pines de conexión (Hardware PINS)
        # Dibujamos líneas de contacto realistas entre el chip y el zócalo
        painter.setPen(QPen(QColor(0, 255, 255, 180), 1.2))
        num_pins = 16
        for i in range(num_pins):
            spacing = 230 / (num_pins - 1)
            # Calculamos posiciones sobre los bordes del rombo
            # Lado Frontal Derecho
            px0 = cx + i * spacing
            py0 = cy + 130 + i * (65/(num_pins-1))
            painter.drawLine(int(px0), int(py0 + 105), int(px0), int(py0 + 120))
            # Lado Frontal Izquierdo
            px1 = cx - i * spacing
            py1 = cy + 130 + i * (65/(num_pins-1))
            painter.drawLine(int(px1), int(py1 + 105), int(px1), int(py1 + 120))

        # 3. El Cuerpo del Chip (Encapsulado de Silicio)
        chip_path = self._create_rhombus(cx, cy + 235, 240, 130)
        # Degradado para superficie metálica/negra
        chip_grad = QLinearGradient(cx - 100, cy + 200, cx + 100, cy + 300)
        chip_grad.setColorAt(0, QColor(10, 12, 30))
        chip_grad.setColorAt(0.5, QColor(5, 5, 15))
        chip_grad.setColorAt(1, QColor(15, 20, 45))
        painter.setBrush(chip_grad)
        painter.setPen(QPen(cyan, 2 + pulse))
        painter.drawPath(chip_path)
        
        # Marcado láser técnico
        painter.setPen(QColor(0, 255, 255, 80))
        painter.setFont(QFont("Segoe UI Semibold", 9))
        painter.drawText(int(cx - 70), int(cy + 250), "VAULT-CORE SECURE")
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(int(cx - 70), int(cy + 265), "SER: PG2026-X86-64")

    def _create_rhombus(self, cx, cy, w, h):
        path = QPainterPath()
        path.moveTo(cx, cy - h)
        path.lineTo(cx + w, cy)
        path.lineTo(cx, cy + h)
        path.lineTo(cx - w, cy)
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx, cy = self.width() / 2, self.height() / 2 - 80
        pulse = (math.sin(self._pulse_time) + 1) / 2
        cyan = QColor(0, 255, 255)
        
        # --- 1. FONDO Y SUELO HIPERREALISTA ---
        self._draw_hyper_floor(painter, cx, cy, pulse)
        
        # --- 2. EL PROCESADOR (CHIP) ---
        self._draw_processor(painter, cx, cy, pulse)

        # --- 3. ATMÓSFERA Y GLOW ---
        glow = QRadialGradient(cx, cy, 300 + 40 * pulse)
        glow.setColorAt(0, QColor(0, 120, 255, int(70 + 30 * pulse)))
        glow.setColorAt(1, Qt.transparent)
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - 400), int(cy - 400), 800, 800)

        # --- 4. LA ESFERA (DATA NUCLEUS) ---
        r = 165
        sphere_grad = QRadialGradient(cx - 50, cy - 50, r * 1.6)
        sphere_grad.setColorAt(0, QColor(0, 240, 255, 220))
        sphere_grad.setColorAt(0.4, QColor(0, 100, 255, 230))
        sphere_grad.setColorAt(1, QColor(0, 15, 50, 255))
        painter.setBrush(sphere_grad)
        painter.setPen(QPen(cyan, 1.5))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # --- 5. CIRCUITOS INTERNOS MULTICAPA (Chips 3D) ---
        for ic in self.internal_chips:
            p = ic['pos']
            rx = p[0] * math.cos(self._angle_y) - p[2] * math.sin(self._angle_y)
            rz = p[0] * math.sin(self._angle_y) + p[2] * math.cos(self._angle_y)
            ry = p[1]
            
            if rz > -60: # Efecto de profundidad de cristal
                factor = 450 / (450 - rz)
                px, py = rx * factor + cx, ry * factor + cy
                alpha = int(220 * (rz+100)/200 * (0.6 + 0.4 * pulse))
                painter.setPen(QPen(QColor(0, 255, 255, alpha), 1))
                painter.setBrush(QColor(0, 255, 255, int(alpha * 0.15)))
                w, h = ic['size'][0] * factor, ic['size'][1] * factor
                painter.drawRect(QRectF(px - w/2, py - h/2, w, h))
                
                # 'Vias' y micro-contactos en el silicio interno
                if rz > 40:
                    painter.setPen(QPen(QColor(255, 255, 255, int(alpha/2)), 0.5))
                    painter.drawLine(int(px - w/2), int(py - h/3), int(px + w/2), int(py - h/3))

        # --- 6. HUD SUPERFICIAL DINÁMICO ---
        hud_pen = QPen(QColor(255, 255, 255, 100), 1)
        painter.setPen(hud_pen)
        painter.drawArc(QRectF(cx - r, cy - r, r*2, r*2), int(self._angle_y * 1200), 35 * 16)
        
        # --- 7. LENS HIGHLIGHT (REFLEJO) ---
        lens = QRadialGradient(cx - 70, cy - 70, 100)
        lens.setColorAt(0, QColor(255, 255, 255, 140))
        lens.setColorAt(1, Qt.transparent)
        painter.setBrush(lens)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx - 70, cy - 70), 85, 85)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HyperRealVaultCore()
    window.show()
    sys.exit(app.exec_())
