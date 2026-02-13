import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QSlider, 
                             QFrame, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt

class NeonProgressBar(QProgressBar):
    def __init__(self, color="#00f2ff", parent=None):
        super().__init__(parent)
        self.setFixedHeight(12)
        self.setTextVisible(False)
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                margin: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
                width: 2px;
            }}
        """)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laboratorio de Estética Neon - Dimmer")
        self.setFixedSize(500, 600)
        self.setStyleSheet("background-color: #0f172a;")
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # --- TARJETA PRINCIPAL ---
        self.card = QFrame()
        self.card.setFixedSize(400, 400) # Un poco más alta para el dimmer
        self.card.setObjectName("NeonCard")
        self.card.setStyleSheet("""
            #NeonCard {
                background-color: rgba(30, 41, 59, 230);
                border: 2px solid #3b82f6;
                border-radius: 20px;
            }
        """)
        
        # Layout interno de la tarjeta
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # --- CONTENEDOR DE DATOS (Lo que se va a desvanecer) ---
        self.content_container = QWidget()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(25)
        
        # Métricas
        self.create_metric(content_layout, "SISTEMA ALPHA", "#00f2ff", 85)
        self.create_metric(content_layout, "CORE TEMPLATE", "#ff00ff", 60)
        self.create_metric(content_layout, "NEON FLUX", "#39ff14", 92)
        
        card_layout.addWidget(self.content_container)
        
        # Separador visual (espacio)
        card_layout.addStretch()
        
        # --- ZONA DEL DIMMER (CONTROL DE OPACIDAD) ---
        dimmer_layout = QVBoxLayout()
        dimmer_layout.setSpacing(10)

        # 1. Etiqueta del porcentaje
        self.lbl_dimmer = QLabel("VISIBILIDAD: 100%")
        self.lbl_dimmer.setAlignment(Qt.AlignCenter)
        self.lbl_dimmer.setStyleSheet("""
            color: #94a3b8; 
            font-size: 11px; 
            font-weight: bold; 
            letter-spacing: 1px;
        """)

        # 2. El Slider (Dimmer)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(10, 100) # Mínimo 10% para que no desaparezca del todo
        self.slider.setValue(100)     # Inicia al 100%
        self.slider.setCursor(Qt.PointingHandCursor)
        
        # Estilo "Cyberpunk" para el slider
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #334155;
                height: 8px;
                background: #0f172a;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6;
                border: 1px solid #3b82f6;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #60a5fa;
                box-shadow: 0 0 10px #3b82f6;
            }
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 4px;
            }
        """)

        # Conectar la señal (evento)
        self.slider.valueChanged.connect(self.update_opacity)

        dimmer_layout.addWidget(self.lbl_dimmer)
        dimmer_layout.addWidget(self.slider)
        
        # Agregar el control a la tarjeta
        card_layout.addLayout(dimmer_layout)
        
        # --- LÓGICA DE OPACIDAD ---
        self.opacity_effect = QGraphicsOpacityEffect(self.content_container)
        self.content_container.setGraphicsEffect(self.opacity_effect)
        
        layout.addWidget(self.card)

    def create_metric(self, layout, name, color, value):
        h_layout = QVBoxLayout()
        h_layout.setSpacing(8)
        
        lbl = QLabel(name)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-family: 'Consolas'; font-size: 14px;")
        
        bar = NeonProgressBar(color)
        bar.setValue(value)
        
        h_layout.addWidget(lbl)
        h_layout.addWidget(bar)
        layout.addLayout(h_layout)

    def update_opacity(self, value):
        # Convertir valor del slider (10-100) a float (0.1 - 1.0)
        opacity_level = value / 100.0
        
        # Aplicar el efecto
        self.opacity_effect.setOpacity(opacity_level)
        
        # Actualizar el texto
        self.lbl_dimmer.setText(f"VISIBILIDAD: {value}%")
        
        # Efecto visual extra: Cambiar color del texto si es muy bajo
        if value < 30:
            self.lbl_dimmer.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold; letter-spacing: 1px;") # Rojo alerta
        else:
            self.lbl_dimmer.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; letter-spacing: 1px;") # Gris normal

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())