# utils.py
import os
import cv2
from PyQt5.QtGui import QPixmap, QImage, QFontDatabase

def convertir_cv_qt(imagen_cv):
    if imagen_cv is None:
        return QPixmap()
    imagen_rgb = cv2.cvtColor(imagen_cv, cv2.COLOR_BGR2RGB)
    height, width, channel = imagen_rgb.shape
    bytes_per_line = channel * width
    q_image = QImage(imagen_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(q_image)

def load_fonts():
    font_path = os.path.join('resources', 'Roboto-Regular.ttf')
    if not os.path.exists(font_path):
        print("Roboto font file not found in resources.")
        return "Arial"
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        print("Failed to load Roboto font.")
        return "Arial"
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    return font_family
