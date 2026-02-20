#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBER DASHBOARD CON DIMMER DE OPACIDAD
======================================
Dashboard estilo cyber-futurista con control de dimmer para ajustar
la transparencia de todos los elementos. Los colores se toman del tema activo.
"""

import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QLinearGradient, 
                        QRadialGradient, QFont, QConicalGradient)


class ThemeColors:
    """Colores del tema - pueden venir de tu ThemeManager"""
    PRIMARY = QColor(0, 255, 136)      # Verde neón
    SECONDARY = QColor(0, 255, 255)    # Cyan
    ACCENT = QColor(255, 0, 255)       # Magenta
    WARNING = QColor(255, 170, 0)      # Naranja
    DANGER = QColor(255, 0, 102)       # Rojo neón
    SUCCESS = QColor(0, 255, 136)      # Verde
    
    BACKGROUND_DARK = QColor(10, 20, 40, 180)
    BACKGROUND_LIGHT = QColor(20, 40, 60, 180)
    
    TEXT_PRIMARY = QColor(255, 255, 255)
    TEXT_SECONDARY = QColor(200, 200, 200)
    
    @staticmethod
    def with_opacity(color, opacity):
        """Aplica opacidad a un color (opacity: 0.0 - 1.0)"""
        new_color = QColor(color)
        new_color.setAlpha(int(255 * opacity))
        return new_color


class DimmerSlider(QWidget):
    """Slider de dimmer con estilo cyber"""
    opacity_changed = pyqtSignal(float)  # Señal cuando cambia la opacidad
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.opacity_value = 100  # 0-100
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Label del dimmer
        self.label = QLabel("🔆 DIMMER CONTROL")
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.PRIMARY.name()};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Courier New';
                letter-spacing: 3px;
                text-transform: uppercase;
            }}
        """)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Slider horizontal
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(20)   # Mínimo 20% opacidad
        self.slider.setMaximum(100)
        self.slider.setValue(100)
        
        primary = ThemeColors.PRIMARY.name()
        secondary = ThemeColors.SECONDARY.name()
        
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 2px solid {primary};
                height: 14px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 26, 13, 200), stop:1 {primary});
                margin: 2px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {secondary}, stop:1 {primary});
                border: 3px solid {primary};
                width: 28px;
                margin: -7px 0;
                border-radius: 14px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {secondary};
                border: 3px solid {secondary};
                box-shadow: 0 0 10px {secondary};
            }}
        """)
        self.slider.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.slider)
        
        # Label del valor
        self.value_label = QLabel("100%")
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.SECONDARY.name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Courier New';
            }}
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        self.setLayout(layout)
        
        bg_dark = f"rgba({ThemeColors.BACKGROUND_DARK.red()}, {ThemeColors.BACKGROUND_DARK.green()}, {ThemeColors.BACKGROUND_DARK.blue()}, {ThemeColors.BACKGROUND_DARK.alpha()})"
        bg_light = f"rgba({ThemeColors.BACKGROUND_LIGHT.red()}, {ThemeColors.BACKGROUND_LIGHT.green()}, {ThemeColors.BACKGROUND_LIGHT.blue()}, {ThemeColors.BACKGROUND_LIGHT.alpha()})"
        
        self.setStyleSheet(f"""
            DimmerSlider {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_dark}, stop:1 {bg_light});
                border: 2px solid {ThemeColors.PRIMARY.name()};
                border-radius: 12px;
            }}
        """)
    
    def on_value_changed(self, value):
        self.opacity_value = value
        self.value_label.setText(f"{value}%")
        
        # Cambiar color del label según valor
        if value < 40:
            color = ThemeColors.DANGER
        elif value < 70:
            color = ThemeColors.WARNING
        else:
            color = ThemeColors.SECONDARY
        
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {color.name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Courier New';
            }}
        """)
        
        # Emitir señal
        self.opacity_changed.emit(value / 100.0)
    
    def get_opacity(self):
        """Retorna opacidad como float 0.0-1.0"""
        return self.opacity_value / 100.0


class MetricsCard(QWidget):
    """Tarjeta 1: Métricas con barra de progreso"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(450, 550)
        self.dimmer_opacity = 1.0
    
    def set_dimmer_opacity(self, opacity):
        """Ajustar opacidad desde el dimmer"""
        self.dimmer_opacity = opacity
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo translúcido con gradiente
        bg_dark = ThemeColors.with_opacity(ThemeColors.BACKGROUND_DARK, self.dimmer_opacity * 0.7)
        bg_light = ThemeColors.with_opacity(ThemeColors.BACKGROUND_LIGHT, self.dimmer_opacity * 0.7)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, bg_dark)
        gradient.setColorAt(1, bg_light)
        
        painter.setBrush(QBrush(gradient))
        border_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(border_color, 3))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        
        # Título
        text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(text_color, 2))
        font = QFont("Arial", 22, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 20, self.width(), 50), Qt.AlignCenter, "SYSTEM METRICS")
        
        # Línea decorativa bajo título
        line_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(line_color, 2))
        painter.drawLine(50, 75, self.width() - 50, 75)
        
        # Métricas
        y_offset = 100
        metrics = [
            ("METRIC 1", "10%", ThemeColors.PRIMARY),
            ("METRIC 2", "12%", ThemeColors.SECONDARY),
            ("METRIC 3", "345", ThemeColors.ACCENT),
        ]
        
        for label, value, color in metrics:
            # Label blanco
            text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
            painter.setPen(QPen(text_color, 2))
            font = QFont("Courier New", 16)
            painter.setFont(font)
            painter.drawText(QRectF(40, y_offset, 200, 40), Qt.AlignLeft | Qt.AlignVCenter, label)
            
            # Valor en color fluorescente
            value_color = ThemeColors.with_opacity(color, self.dimmer_opacity)
            painter.setPen(QPen(value_color, 2))
            font = QFont("Courier New", 20, QFont.Bold)
            painter.setFont(font)
            painter.drawText(QRectF(250, y_offset, 160, 40), Qt.AlignRight | Qt.AlignVCenter, value)
            
            y_offset += 70
        
        # METRIC 4 - Barra de progreso verde (valor 7 de 10)
        y_offset += 20
        
        # Label
        text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(text_color, 2))
        font = QFont("Courier New", 16)
        painter.setFont(font)
        painter.drawText(QRectF(40, y_offset, 200, 40), Qt.AlignLeft | Qt.AlignVCenter, "METRIC 4")
        
        # Barra de progreso
        bar_y = y_offset + 50
        bar_width = 370
        bar_height = 35
        bar_x = 40
        
        # Fondo de la barra
        bg_bar = ThemeColors.with_opacity(QColor(0, 50, 25, 150), self.dimmer_opacity * 0.6)
        painter.setBrush(bg_bar)
        border_bar = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity * 0.5)
        painter.setPen(QPen(border_bar, 2))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 17, 17)
        
        # Progreso (valor 7 de 10)
        progress_value = 7
        progress_width = int((progress_value / 10) * bar_width)
        
        # Gradiente verde intenso para el progreso
        gradient = QLinearGradient(bar_x, bar_y, bar_x + progress_width, bar_y)
        color1 = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        color2 = ThemeColors.with_opacity(ThemeColors.SECONDARY, self.dimmer_opacity)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height, 17, 17)
        
        # Valor numérico sobre la barra
        text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(text_color, 2))
        font = QFont("Courier New", 18, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(bar_x, bar_y, bar_width, bar_height), Qt.AlignCenter, f"{progress_value}/10")
        
        # Borde brillante final
        border_glow = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(border_glow, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 17, 17)


class SonarDonutCard(QWidget):
    """Tarjeta 2: Sonar rotatorio + Donut con valor 65"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(450, 550)
        self.sonar_angle = 0
        self.dimmer_opacity = 1.0
        
        # Timer para animación del sonar
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sonar)
        self.timer.start(50)  # 50ms = 20 FPS
    
    def set_dimmer_opacity(self, opacity):
        """Ajustar opacidad desde el dimmer"""
        self.dimmer_opacity = opacity
        self.update()
    
    def update_sonar(self):
        self.sonar_angle += 4
        if self.sonar_angle >= 360:
            self.sonar_angle = 0
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo translúcido
        bg_dark = ThemeColors.with_opacity(ThemeColors.BACKGROUND_DARK, self.dimmer_opacity * 0.7)
        bg_light = ThemeColors.with_opacity(ThemeColors.BACKGROUND_LIGHT, self.dimmer_opacity * 0.7)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, bg_dark)
        gradient.setColorAt(1, bg_light)
        
        painter.setBrush(QBrush(gradient))
        border_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(border_color, 3))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        
        # Título
        text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(text_color, 2))
        font = QFont("Arial", 22, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 20, self.width(), 50), Qt.AlignCenter, "RADAR SCAN")
        
        # Línea decorativa
        line_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(line_color, 2))
        painter.drawLine(50, 75, self.width() - 50, 75)
        
        # --- SONAR ROTATORIO ---
        sonar_center_x = self.width() // 2
        sonar_center_y = 180
        sonar_radius = 80
        
        # Círculos concéntricos del sonar
        for i in range(3):
            radius = sonar_radius - (i * 25)
            circle_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity * (0.3 - i * 0.1))
            painter.setPen(QPen(circle_color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(sonar_center_x, sonar_center_y), radius, radius)
        
        # Línea del sonar rotando
        angle_rad = math.radians(self.sonar_angle)
        end_x = sonar_center_x + sonar_radius * math.cos(angle_rad)
        end_y = sonar_center_y + sonar_radius * math.sin(angle_rad)
        
        # Gradiente cónico para efecto de barrido
        gradient = QConicalGradient(sonar_center_x, sonar_center_y, self.sonar_angle - 90)
        gradient.setColorAt(0, ThemeColors.with_opacity(ThemeColors.PRIMARY, 0))
        gradient.setColorAt(0.5, ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity * 0.8))
        gradient.setColorAt(1, ThemeColors.with_opacity(ThemeColors.PRIMARY, 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawPie(
            sonar_center_x - sonar_radius, 
            sonar_center_y - sonar_radius, 
            sonar_radius * 2, 
            sonar_radius * 2, 
            0, 360 * 16
        )
        
        # Línea verde brillante del sonar
        line_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(line_color, 3))
        painter.drawLine(sonar_center_x, sonar_center_y, int(end_x), int(end_y))
        
        # --- DONUT CON VALOR 65 ---
        donut_center_y = 400
        donut_outer_radius = 90
        donut_inner_radius = 65
        
        # Donut con gradiente fluorescente
        gradient = QRadialGradient(sonar_center_x, donut_center_y, donut_outer_radius)
        
        # Colores fluorescentes intensos
        color1 = ThemeColors.with_opacity(ThemeColors.ACCENT, self.dimmer_opacity)      # Magenta
        color2 = ThemeColors.with_opacity(ThemeColors.SECONDARY, self.dimmer_opacity)   # Cyan
        color3 = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)     # Verde
        
        gradient.setColorAt(0, color1)
        gradient.setColorAt(0.5, color2)
        gradient.setColorAt(1, color3)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(
            QPointF(sonar_center_x, donut_center_y), 
            donut_outer_radius, 
            donut_outer_radius
        )
        
        # Centro negro del donut (para hacer el agujero)
        center_bg = ThemeColors.with_opacity(QColor(10, 20, 40, 250), self.dimmer_opacity * 0.9)
        painter.setBrush(center_bg)
        painter.drawEllipse(
            QPointF(sonar_center_x, donut_center_y), 
            donut_inner_radius, 
            donut_inner_radius
        )
        
        # Valor 65 en el centro
        text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(text_color, 2))
        font = QFont("Arial", 48, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(sonar_center_x - 60, donut_center_y - 30, 120, 60), 
            Qt.AlignCenter, 
            "65"
        )
        
        # Borde brillante del donut
        border_color = ThemeColors.with_opacity(ThemeColors.SECONDARY, self.dimmer_opacity)
        painter.setPen(QPen(border_color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            QPointF(sonar_center_x, donut_center_y), 
            donut_outer_radius, 
            donut_outer_radius
        )


class AlertCard(QWidget):
    """Tarjeta 3: Número 18 con círculo rojo de alerta"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(450, 550)
        self.dimmer_opacity = 1.0
        self.pulse_value = 0
        
        # Timer para efecto de pulso
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_pulse)
        self.timer.start(30)
    
    def set_dimmer_opacity(self, opacity):
        """Ajustar opacidad desde el dimmer"""
        self.dimmer_opacity = opacity
        self.update()
    
    def update_pulse(self):
        self.pulse_value += 0.05
        if self.pulse_value >= 2 * math.pi:
            self.pulse_value = 0
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo translúcido
        bg_dark = ThemeColors.with_opacity(ThemeColors.BACKGROUND_DARK, self.dimmer_opacity * 0.7)
        bg_light = ThemeColors.with_opacity(ThemeColors.BACKGROUND_LIGHT, self.dimmer_opacity * 0.7)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, bg_dark)
        gradient.setColorAt(1, bg_light)
        
        painter.setBrush(QBrush(gradient))
        border_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(border_color, 3))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        
        # Título
        text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(text_color, 2))
        font = QFont("Arial", 22, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 20, self.width(), 50), Qt.AlignCenter, "ALERT STATUS")
        
        # Línea decorativa
        line_color = ThemeColors.with_opacity(ThemeColors.PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(line_color, 2))
        painter.drawLine(50, 75, self.width() - 50, 75)
        
        # Centro de la tarjeta
        center_x = self.width() // 2
        center_y = 300
        
        # Efecto de pulso (variar radio)
        pulse_factor = 1 + 0.1 * math.sin(self.pulse_value)
        
        # Círculos concéntricos de advertencia
        for i in range(3):
            radius = (120 + i * 25) * pulse_factor
            alpha = self.dimmer_opacity * (0.2 - i * 0.05)
            circle_color = ThemeColors.with_opacity(ThemeColors.DANGER, alpha)
            painter.setPen(QPen(circle_color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
        
        # Círculo principal ROJO con gradiente
        main_radius = 110
        gradient = QRadialGradient(center_x, center_y, main_radius)
        
        danger_center = ThemeColors.with_opacity(ThemeColors.DANGER, self.dimmer_opacity * 0.8)
        danger_edge = ThemeColors.with_opacity(ThemeColors.DANGER, self.dimmer_opacity * 0.4)
        
        gradient.setColorAt(0, danger_center)
        gradient.setColorAt(1, danger_edge)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(center_x, center_y), main_radius, main_radius)
        
        # Borde del círculo rojo brillante
        border_red = ThemeColors.with_opacity(ThemeColors.DANGER, self.dimmer_opacity)
        painter.setPen(QPen(border_red, 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(center_x, center_y), main_radius, main_radius)
        
        # Número 18 en el centro
        text_color = ThemeColors.with_opacity(ThemeColors.TEXT_PRIMARY, self.dimmer_opacity)
        painter.setPen(QPen(text_color, 3))
        font = QFont("Arial", 80, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(center_x - 80, center_y - 50, 160, 100), 
            Qt.AlignCenter, 
            "18"
        )
        
        # Texto de advertencia
        painter.setPen(QPen(text_color, 2))
        font = QFont("Courier New", 16, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, center_y + 140, self.width(), 40), 
            Qt.AlignCenter, 
            "⚠ CRITICAL ALERT ⚠"
        )


class CyberDashboard(QMainWindow):
    """Ventana principal con dashboard y dimmer"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyber Dashboard con Dimmer")
        self.setGeometry(100, 100, 1400, 800)
        
        # Fondo oscuro principal
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgb(5, 10, 20),
                    stop:1 rgb(10, 20, 40));
            }
        """)
        
        self.initUI()
    
    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Dimmer en la parte superior
        self.dimmer = DimmerSlider()
        self.dimmer.opacity_changed.connect(self.on_opacity_changed)
        main_layout.addWidget(self.dimmer)
        
        # Grid con las 3 tarjetas
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Tarjeta 1: Métricas
        self.metrics_card = MetricsCard()
        cards_layout.addWidget(self.metrics_card)
        
        # Tarjeta 2: Sonar + Donut
        self.sonar_card = SonarDonutCard()
        cards_layout.addWidget(self.sonar_card)
        
        # Tarjeta 3: Alerta con 18
        self.alert_card = AlertCard()
        cards_layout.addWidget(self.alert_card)
        
        main_layout.addLayout(cards_layout)
        
        central_widget.setLayout(main_layout)
    
    def on_opacity_changed(self, opacity):
        """Cuando el dimmer cambia, actualizar opacidad de todas las tarjetas"""
        self.metrics_card.set_dimmer_opacity(opacity)
        self.sonar_card.set_dimmer_opacity(opacity)
        self.alert_card.set_dimmer_opacity(opacity)


def main():
    app = QApplication(sys.argv)
    
    # Configurar fuente global
    app.setFont(QFont("Arial", 10))
    
    window = CyberDashboard()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()