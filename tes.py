import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QPushButton, 
                             QFrame, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

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
        self.setWindowTitle("Laboratorio de Estética Neon")
        self.setFixedSize(500, 600)
        self.setStyleSheet("background-color: #0f172a;")
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Card Container
        self.card = QFrame()
        self.card.setFixedSize(400, 350)
        self.card.setObjectName("NeonCard")
        self.card.setStyleSheet("""
            #NeonCard {
                background-color: rgba(30, 41, 59, 230);
                border: 2px solid #3b82f6;
                border-radius: 20px;
            }
        """)
        
        # Inner layout for the card
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # Container for content (to apply opacity easily)
        self.content_container = QWidget()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(25)
        
        # Labels and Bars
        self.create_metric(content_layout, "SISTEMA ALPHA", "#00f2ff", 85)
        self.create_metric(content_layout, "CORE TEMPLATE", "#ff00ff", 60)
        self.create_metric(content_layout, "NEON FLUX", "#39ff14", 92)
        
        card_layout.addWidget(self.content_container)
        
        # Button to toggle translucency
        self.btn_toggle = QPushButton("ALTERNAR TRASLUCIDEZ")
        self.btn_toggle.setFixedSize(250, 45)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_toggle.clicked.connect(self.toggle_transparency)
        
        card_layout.addStretch()
        card_layout.addWidget(self.btn_toggle, alignment=Qt.AlignCenter)
        
        layout.addWidget(self.card)
        
        # Opacity Logic
        self.opacity_effect = QGraphicsOpacityEffect(self.content_container)
        self.content_container.setGraphicsEffect(self.opacity_effect)
        self.is_translucent = False

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

    def toggle_transparency(self):
        # Animación suave de opacidad
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        if self.is_translucent:
            self.anim.setStartValue(0.2)
            self.anim.setEndValue(1.0)
            self.is_translucent = False
        else:
            self.anim.setStartValue(1.0)
            self.anim.setEndValue(0.2)
            self.is_translucent = True
            
        self.anim.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
