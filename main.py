# main.py
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from app import VentanaPrincipal
from utils import load_fonts

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Load Roboto Font
    font_family = load_fonts()
    app.setFont(QFont(font_family, 12))
    ventana = VentanaPrincipal()
    ventana.showMaximized()
    sys.exit(app.exec_())
