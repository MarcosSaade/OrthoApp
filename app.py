# app.py
import os
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QWidget, QMessageBox, QSizePolicy, QAction, QDialog, QSpacerItem
)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QIcon
from PyQt5.QtCore import Qt, QSettings
from utils import convertir_cv_qt, load_fonts
from ui_components import PatientInfoDialog, ConfirmationDialog
from image_processing import procesar_imagen
from pdf_report import generate_pdf_report
from scanner import scan_image


TEST_MODE = True  # Set to True for testing (uploads images), False for production (scans images)


class AspectRatioLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scaled_pixmap = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (self.width() - scaled_pixmap.width()) / 2
            y = (self.height() - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orto-Flex Scanner")
        
        # Set the window icon
        icon_path = os.path.join('resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon file not found at {icon_path}. Using default icon.")

        # Initialize image variables
        self.left_image_original = None
        self.left_image_processed = None
        self.right_image_original = None
        self.right_image_processed = None

        # Load user preferences
        self.settings = QSettings("OrtoFlex", "ScannerApp")
        self.load_preferences()

        self.last_directory = self.settings.value("last_directory", os.path.expanduser("~"))
        self.last_pdf_directory = self.settings.value("last_pdf_directory", self.last_directory)

        # Load Roboto Font
        self.font_family = load_fonts()

        # Initialize UI components
        self.inicializar_componentes()
        self.aplicar_estilos()

        # Show application in fullscreen
        self.showFullScreen()

    def inicializar_componentes(self):
        # Menu Bar
        self.menu_bar = self.menuBar()
        self.crear_menu()

        # Image Labels
        self.label_imagen_izquierda = AspectRatioLabel()
        self.label_imagen_izquierda.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")

        self.label_imagen_derecha = AspectRatioLabel()
        self.label_imagen_derecha.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")

        # Load initial background images
        bg_left_path = os.path.join('resources', 'bg_left.png')
        if os.path.exists(bg_left_path):
            pixmap_bg_left = QPixmap(bg_left_path)
            self.label_imagen_izquierda.setPixmap(pixmap_bg_left)
        else:
            self.label_imagen_izquierda.setText("Pie Izquierdo")
            self.label_imagen_izquierda.setFont(QFont(self.font_family, 16))
            self.label_imagen_izquierda.setStyleSheet("color: #1d3557;")

        bg_right_path = os.path.join('resources', 'bg_right.png')
        if os.path.exists(bg_right_path):
            pixmap_bg_right = QPixmap(bg_right_path)
            self.label_imagen_derecha.setPixmap(pixmap_bg_right)
        else:
            self.label_imagen_derecha.setText("Pie Derecho")
            self.label_imagen_derecha.setFont(QFont(self.font_family, 16))
            self.label_imagen_derecha.setStyleSheet("color: #1d3557;")

        # Images Layout
        imagenes_layout = QHBoxLayout()
        imagenes_layout.addWidget(self.label_imagen_izquierda)
        imagenes_layout.addWidget(self.label_imagen_derecha)
        imagenes_layout.setStretch(0, 1)
        imagenes_layout.setStretch(1, 1)
        imagenes_layout.setSpacing(40)

        # Buttons
        if TEST_MODE:
            self.boton_cargar_izquierdo = QPushButton("Cargar Pie Izquierdo")
            self.boton_cargar_izquierdo.clicked.connect(self.cargar_imagen_izquierda)
            self.boton_cargar_izquierdo.setToolTip("Cargar imagen del pie izquierdo")
        else:
            self.boton_cargar_izquierdo = QPushButton("Escanear Pie Izquierdo")
            self.boton_cargar_izquierdo.clicked.connect(self.escanear_imagen_izquierda)
            self.boton_cargar_izquierdo.setToolTip("Escanear el pie izquierdo")

        if TEST_MODE:
            self.boton_cargar_derecho = QPushButton("Cargar Pie Derecho")
            self.boton_cargar_derecho.clicked.connect(self.cargar_imagen_derecha)
            self.boton_cargar_derecho.setToolTip("Cargar imagen del pie derecho")
        else:
            self.boton_cargar_derecho = QPushButton("Escanear Pie Derecho")
            self.boton_cargar_derecho.clicked.connect(self.escanear_imagen_derecha)
            self.boton_cargar_derecho.setToolTip("Escanear el pie derecho")

        # Set button properties
        for boton in [self.boton_cargar_izquierdo, self.boton_cargar_derecho]:
            boton.setFixedSize(200, 50)
            boton.setFont(QFont(self.font_family, 14))
            boton.setObjectName('boton_cargar')

        self.boton_generar_reporte = QPushButton("Generar Reporte")
        self.boton_generar_reporte.clicked.connect(self.generar_reporte)
        self.boton_generar_reporte.setFixedSize(200, 50)
        self.boton_generar_reporte.setToolTip("Generar reporte PDF")
        self.boton_generar_reporte.setFont(QFont(self.font_family, 14))
        self.boton_generar_reporte.setEnabled(False)
        self.boton_generar_reporte.setObjectName('boton_generar_reporte')

        # Buttons Layout
        botones_layout = QHBoxLayout()
        botones_layout.setContentsMargins(0, 0, 0, 0)
        botones_layout.addStretch()
        botones_layout.addWidget(self.boton_cargar_izquierdo)
        botones_layout.addWidget(self.boton_cargar_derecho)
        botones_layout.addWidget(self.boton_generar_reporte)
        botones_layout.addStretch()
        botones_layout.setSpacing(40)

        # Spacer
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(imagenes_layout)
        main_layout.addItem(spacer)
        main_layout.addLayout(botones_layout)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 0)
        main_layout.setStretch(2, 0)

        contenedor = QWidget()
        contenedor.setLayout(main_layout)
        self.setCentralWidget(contenedor)

    def crear_menu(self):
        self.menu_bar = self.menuBar()
        nuevo_action = QAction("Nuevo", self)
        nuevo_action.triggered.connect(self.nuevo)
        self.menu_bar.addAction(nuevo_action)

        help_menu = self.menu_bar.addMenu("Ayuda")

        help_action = QAction("Instrucciones", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        about_action = QAction("Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def aplicar_estilos(self):
        estilo = """
        QMainWindow {
            background-color: #e8eff5;
        }
        QLabel#label_titulo {
            color: #1d3557;
            font-weight: bold;
            font-family: 'Roboto', sans-serif;
        }
        QPushButton#boton_cargar, QPushButton#boton_generar_reporte {
            background-color: #3e4095;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-size: 14px;
            font-weight: 500;
            font-family: 'Roboto', sans-serif;
        }
        QPushButton#boton_cargar:hover, QPushButton#boton_generar_reporte:hover {
            background-color: #e0262d;
        }
        QPushButton#boton_cargar:pressed, QPushButton#boton_generar_reporte:pressed {
            background-color: #c92028;
        }
        QLabel {
            color: #1d3557;
            font-family: 'Roboto', sans-serif;
        }
        QMenuBar {
            font-family: 'Roboto', sans-serif;
            font-size: 16px;
        }
        QMenu {
            font-family: 'Roboto', sans-serif;
            font-size: 16px;
        }
        """
        self.setStyleSheet(estilo)

    def cargar_imagen_izquierda(self):
        opciones = QFileDialog.Options()
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen del Pie Izquierdo", self.last_directory,
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.svg)", options=opciones
        )
        if ruta_archivo:
            try:
                self.last_directory = os.path.dirname(ruta_archivo)
                self.settings.setValue("last_directory", self.last_directory)

                self.left_image_original = cv2.imread(ruta_archivo)
                if self.left_image_original is None:
                    raise Exception("No se pudo cargar la imagen.")

                self.left_image_processed = procesar_imagen(
                    ruta=ruta_archivo, ruta_logotipo=None, recolor=True, image=None, foot_side="left"
                )

                pixmap = convertir_cv_qt(self.left_image_processed)
                self.display_left_image(pixmap)

                if self.left_image_original is not None and self.right_image_original is not None:
                    self.boton_generar_reporte.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo procesar la imagen.\n{str(e)}")

    def cargar_imagen_derecha(self):
        opciones = QFileDialog.Options()
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen del Pie Derecho", self.last_directory,
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.svg)", options=opciones
        )
        if ruta_archivo:
            try:
                self.last_directory = os.path.dirname(ruta_archivo)
                self.settings.setValue("last_directory", self.last_directory)

                self.right_image_original = cv2.imread(ruta_archivo)
                if self.right_image_original is None:
                    raise Exception("No se pudo cargar la imagen.")

                self.right_image_processed = procesar_imagen(
                    ruta=ruta_archivo, ruta_logotipo=None, recolor=True, image=None, foot_side="right"
                )

                pixmap = convertir_cv_qt(self.right_image_processed)
                self.display_right_image(pixmap)

                if self.left_image_original is not None and self.right_image_original is not None:
                    self.boton_generar_reporte.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo procesar la imagen.\n{str(e)}")

    def escanear_imagen_izquierda(self):
        try:
            self.left_image_original = scan_image()
            if self.left_image_original is None:
                raise Exception("No se pudo escanear la imagen.")

            self.left_image_original = cv2.rotate(self.left_image_original, cv2.ROTATE_180)

            self.left_image_processed = procesar_imagen(
                ruta=None, ruta_logotipo=None, recolor=True, image=self.left_image_original, foot_side="left"
            )

            pixmap = convertir_cv_qt(self.left_image_processed)
            self.display_left_image(pixmap)

            if self.left_image_original is not None and self.right_image_original is not None:
                self.boton_generar_reporte.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo escanear o procesar la imagen.\n{str(e)}")

    def escanear_imagen_derecha(self):
        try:
            self.right_image_original = scan_image()
            if self.right_image_original is None:
                raise Exception("No se pudo escanear la imagen.")

            self.right_image_original = cv2.rotate(self.right_image_original, cv2.ROTATE_180)

            self.right_image_processed = procesar_imagen(
                ruta=None, ruta_logotipo=None, recolor=True, image=self.right_image_original, foot_side="right"
            )

            pixmap = convertir_cv_qt(self.right_image_processed)
            self.display_right_image(pixmap)

            if self.left_image_original is not None and self.right_image_original is not None:
                self.boton_generar_reporte.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo escanear o procesar la imagen.\n{str(e)}")

    def display_left_image(self, pixmap):
        self.label_imagen_izquierda.setPixmap(pixmap)

    def display_right_image(self, pixmap):
        self.label_imagen_derecha.setPixmap(pixmap)

    def generar_reporte(self):
        if self.left_image_original is None or self.right_image_original is None:
            QMessageBox.warning(self, "Advertencia", "Debe cargar o escanear las imágenes de ambos pies.")
            return

        # Initialize variables to hold patient info
        patient_info = {
            'paciente': '',
            'telefono': '',
            'longitud_pie': '',
            'material': '',
            'entrega_date': '',
            'fecha_escaneo': '',
            'sucursal': '',
            'taller': '',
            'order_number': '',
            'observaciones': ''
        }

        while True:
            dialog = PatientInfoDialog(
                paciente=patient_info['paciente'],
                telefono=patient_info['telefono'],
                longitud_pie=patient_info['longitud_pie'],
                material=patient_info['material'],
                entrega_date=patient_info['entrega_date'],
                fecha_escaneo=patient_info['fecha_escaneo'],
                sucursal=patient_info['sucursal'],
                taller=patient_info['taller'],
                order_number=patient_info['order_number'],
                observaciones=patient_info['observaciones']
            )
            if dialog.exec_() == QDialog.Accepted:
                # Retrieve data from dialog
                paciente = dialog.paciente_edit.text()
                telefono = dialog.telefono_edit.text()
                longitud_pie = dialog.longitud_edit.text()
                material = dialog.get_material()
                entrega_date = dialog.get_fecha_entrega().strftime("%d/%m/%Y")
                fecha_escaneo = dialog.fecha_escaneo_edit.date().toString("dd/MM/yyyy")
                sucursal = dialog.sucursal_edit.currentText()
                taller = dialog.taller_edit.currentText()
                order_number = dialog.order_number_edit.text()
                observaciones = dialog.observaciones_edit.toPlainText()

                # Update patient_info with current data
                patient_info.update({
                    'paciente': paciente,
                    'telefono': telefono,
                    'longitud_pie': longitud_pie,
                    'material': material,
                    'entrega_date': entrega_date,
                    'fecha_escaneo': fecha_escaneo,
                    'sucursal': sucursal,
                    'taller': taller,
                    'order_number': order_number,
                    'observaciones': observaciones
                })

                # Show Confirmation Dialog
                confirm_dialog = ConfirmationDialog(
                    paciente=paciente,
                    telefono=telefono,
                    longitud_pie=longitud_pie,
                    material=material,
                    entrega_date=entrega_date,
                    fecha_escaneo=fecha_escaneo,
                    sucursal=sucursal,
                    taller=taller,
                    order_number=order_number,
                    observaciones=observaciones
                )
                if confirm_dialog.exec_() == QDialog.Accepted:
                    ruta_logotipo = os.path.join('resources', 'logo_square.png')

                    left_skin_image = procesar_imagen(
                        ruta=None, ruta_logotipo=ruta_logotipo, recolor=False, image=self.left_image_original, foot_side="left"
                    )
                    left_heatmap_image = procesar_imagen(
                        ruta=None, ruta_logotipo=ruta_logotipo, recolor=True, image=self.left_image_original, foot_side="left"
                    )

                    right_skin_image = procesar_imagen(
                        ruta=None, ruta_logotipo=ruta_logotipo, recolor=False, image=self.right_image_original, foot_side="right"
                    )
                    right_heatmap_image = procesar_imagen(
                        ruta=None, ruta_logotipo=ruta_logotipo, recolor=True, image=self.right_image_original, foot_side="right"
                    )

                    try:
                        ruta_pdf = generate_pdf_report(
                            paciente=paciente,
                            telefono=telefono,
                            order_number=order_number,
                            sucursal=sucursal,
                            taller=taller,
                            longitud_pie=longitud_pie,
                            material=material,
                            observaciones=observaciones,
                            left_skin_image=left_skin_image,
                            right_skin_image=right_skin_image,
                            left_heatmap_image=left_heatmap_image,
                            right_heatmap_image=right_heatmap_image,
                            left_original_image=self.left_image_original,
                            right_original_image=self.right_image_original,
                            last_pdf_directory=self.last_pdf_directory,
                            fecha_escaneo=fecha_escaneo,
                            fecha_entrega=entrega_date
                        )
                        QMessageBox.information(self, "Éxito", "Reporte PDF generado exitosamente.")

                        # Update last_pdf_directory
                        if ruta_pdf:
                            self.last_pdf_directory = os.path.dirname(ruta_pdf)
                            self.settings.setValue("last_pdf_directory", self.last_pdf_directory)

                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"No se pudo generar el reporte PDF.\n{str(e)}")
                    break  # Exit the loop after successful report generation
                else:
                    # User chose to cancel and return to editing patient info
                    continue  # Re-open PatientInfoDialog with existing data
            else:
                # User canceled the PatientInfoDialog
                break

    def show_help(self):
        help_text = (
            "Instrucciones de Uso:\n\n"
            f"1. {'Cargar' if TEST_MODE else 'Escanear'} Pie Izquierdo: "
            f"{'Seleccione una imagen del pie izquierdo.' if TEST_MODE else 'Escanee la imagen del pie izquierdo.'}\n"
            f"2. {'Cargar' if TEST_MODE else 'Escanear'} Pie Derecho: "
            f"{'Seleccione una imagen del pie derecho.' if TEST_MODE else 'Escanee la imagen del pie derecho.'}\n"
            "3. Generar Reporte: Genere un reporte PDF con las imágenes procesadas.\n\n"
            "Presione 'Esc' para salir del modo de pantalla maximizada."
        )
        QMessageBox.information(self, "Ayuda", help_text)

    def show_about(self):
        about_text = (
            "Orto Flex Scanner\n\n"
            "Versión 1.0\n\n"
            "Desarrollado por Marcos Saade.\n"
            "© 2024 Todos los derechos reservados."
        )
        QMessageBox.information(self, "Acerca de", about_text)

    def load_preferences(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_preferences(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_directory", self.last_directory)
        self.settings.setValue("last_pdf_directory", self.last_pdf_directory)

    def closeEvent(self, event):
        self.save_preferences()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        else:
            super().keyPressEvent(event)

    def nuevo(self):
        self.left_image_original = None
        self.left_image_processed = None
        self.right_image_original = None
        self.right_image_processed = None

        bg_left_path = os.path.join('resources', 'bg_left.png')
        if os.path.exists(bg_left_path):
            pixmap_bg_left = QPixmap(bg_left_path)
            self.label_imagen_izquierda.setPixmap(pixmap_bg_left)
        else:
            self.label_imagen_izquierda.setText("Pie Izquierdo")
            self.label_imagen_izquierda.setFont(QFont(self.font_family, 16))
            self.label_imagen_izquierda.setStyleSheet("color: #1d3557;")

        bg_right_path = os.path.join('resources', 'bg_right.png')
        if os.path.exists(bg_right_path):
            pixmap_bg_right = QPixmap(bg_right_path)
            self.label_imagen_derecha.setPixmap(pixmap_bg_right)
        else:
            self.label_imagen_derecha.setText("Pie Derecho")
            self.label_imagen_derecha.setFont(QFont(self.font_family, 16))
            self.label_imagen_derecha.setStyleSheet("color: #1d3557;")

        self.boton_generar_reporte.setEnabled(False)


def main():
    import sys
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
