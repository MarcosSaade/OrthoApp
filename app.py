# app.py
import os
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QWidget, QMessageBox, QSizePolicy, QAction, QDialog
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QSettings
from utils import convertir_cv_qt, load_fonts
from ui_components import PatientInfoDialog
from image_processing import procesar_imagen
from pdf_report import generate_pdf_report
from scanner import scan_image


# Define TEST_MODE
TEST_MODE = True  # Set to True for testing (uploads images), False for production (scans images)


class AspectRatioLabel(QLabel):
    """
    Custom QLabel that maintains the aspect ratio of the pixmap.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(self._scaled_pixmap())

    def resizeEvent(self, event):
        if self._pixmap:
            super().setPixmap(self._scaled_pixmap())
        super().resizeEvent(event)

    def _scaled_pixmap(self):
        return self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orto-Flex Scanner")

        # Initialize image variables
        self.left_image_original = None
        self.left_image_processed = None
        self.right_image_original = None
        self.right_image_processed = None

        # Load user preferences
        self.settings = QSettings("OrtoFlex", "ScannerApp")
        self.load_preferences()

        self.last_directory = self.settings.value("last_directory", os.path.expanduser("~"))

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

        # Header Layout: Logo Only (Removed "Scanner" Label)
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Clinic Logo (Smaller Size)
        self.label_logo = QLabel()
        self.label_logo.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join('resources', 'logo.png')  # Ensure 'logo.png' exists in 'resources' folder
        if os.path.exists(logo_path):
            pixmap_logo = QPixmap(logo_path)
            pixmap_logo = pixmap_logo.scaledToHeight(60, Qt.SmoothTransformation)  # Further reduced height to 60
            self.label_logo.setPixmap(pixmap_logo)
        else:
            self.label_logo.setText("Logo")
            self.label_logo.setFont(QFont(self.font_family, 14))  # Adjusted font size
            self.label_logo.setStyleSheet("color: #1d3557;")

        # Add logo to header layout
        header_layout.addWidget(self.label_logo)

        # Image Labels for Left and Right Foot
        self.label_imagen_izquierda = AspectRatioLabel()
        self.label_imagen_izquierda.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")
        self.label_imagen_izquierda.setFixedSize(600, 700)  # Slightly taller than square

        self.label_imagen_derecha = AspectRatioLabel()
        self.label_imagen_derecha.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")
        self.label_imagen_derecha.setFixedSize(600, 700)  # Slightly taller than square

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

        # Images Layout (Side by Side)
        imagenes_layout = QHBoxLayout()
        imagenes_layout.addWidget(self.label_imagen_izquierda)
        imagenes_layout.addWidget(self.label_imagen_derecha)
        imagenes_layout.setStretch(0, 1)
        imagenes_layout.setStretch(1, 1)
        imagenes_layout.setSpacing(40)  # Increased spacing for better appearance

        # Buttons: Upload or Scan Left Foot, Upload or Scan Right Foot, Generate Report
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

        self.boton_cargar_izquierdo.setFixedSize(200, 50)
        self.boton_cargar_izquierdo.setFont(QFont(self.font_family, 14))
        self.boton_cargar_izquierdo.setObjectName('boton_cargar')

        self.boton_cargar_derecho.setFixedSize(200, 50)
        self.boton_cargar_derecho.setFont(QFont(self.font_family, 14))
        self.boton_cargar_derecho.setObjectName('boton_cargar')

        self.boton_generar_reporte = QPushButton("Generar Reporte")
        self.boton_generar_reporte.clicked.connect(self.generar_reporte)
        self.boton_generar_reporte.setFixedSize(200, 50)
        self.boton_generar_reporte.setToolTip("Generar reporte PDF")
        self.boton_generar_reporte.setFont(QFont(self.font_family, 14))
        self.boton_generar_reporte.setEnabled(False)
        self.boton_generar_reporte.setObjectName('boton_generar_reporte')

        # Buttons Layout
        botones_layout = QHBoxLayout()
        botones_layout.setContentsMargins(0, 30, 0, 30)
        botones_layout.addStretch()
        botones_layout.addWidget(self.boton_cargar_izquierdo)
        botones_layout.addWidget(self.boton_cargar_derecho)
        botones_layout.addWidget(self.boton_generar_reporte)
        botones_layout.addStretch()
        botones_layout.setSpacing(40)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addLayout(imagenes_layout)
        main_layout.addLayout(botones_layout)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Set Central Widget
        contenedor = QWidget()
        contenedor.setLayout(main_layout)
        self.setCentralWidget(contenedor)

    def crear_menu(self):
        # Menu Bar
        self.menu_bar = self.menuBar()

        # Nuevo Action
        nuevo_action = QAction("Nuevo", self)
        nuevo_action.triggered.connect(self.nuevo)
        self.menu_bar.addAction(nuevo_action)

        # Help Menu
        help_menu = self.menu_bar.addMenu("Ayuda")

        # Help Action
        help_action = QAction("Instrucciones", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        # About Action
        about_action = QAction("Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def aplicar_estilos(self):
        # Style Sheet for the application
        estilo = """
        QMainWindow {
            background-color: #FFFFFF;  /* Changed to white */
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
        """
        Upload the left foot image using a file dialog.
        """
        opciones = QFileDialog.Options()
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen del Pie Izquierdo", self.last_directory,
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.svg)", options=opciones
        )
        if ruta_archivo:
            try:
                # Update last directory
                self.last_directory = os.path.dirname(ruta_archivo)
                self.settings.setValue("last_directory", self.last_directory)

                # Load original image
                self.left_image_original = cv2.imread(ruta_archivo)
                if self.left_image_original is None:
                    raise Exception("No se pudo cargar la imagen.")

                # Process image with recoloring (heatmap)
                self.left_image_processed = procesar_imagen(
                    ruta_archivo, None, recolor=True, foot_side="left"
                )

                # Convert to QPixmap and display on the left side
                pixmap = convertir_cv_qt(self.left_image_processed)
                self.display_left_image(pixmap)

                # Check if both images are loaded to enable 'Generar Reporte' button
                if self.left_image_original is not None and self.right_image_original is not None:
                    self.boton_generar_reporte.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo procesar la imagen.\n{str(e)}")

    def cargar_imagen_derecha(self):
        """
        Upload the right foot image using a file dialog.
        """
        opciones = QFileDialog.Options()
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen del Pie Derecho", self.last_directory,
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.svg)", options=opciones
        )
        if ruta_archivo:
            try:
                # Update last directory
                self.last_directory = os.path.dirname(ruta_archivo)
                self.settings.setValue("last_directory", self.last_directory)

                # Load original image
                self.right_image_original = cv2.imread(ruta_archivo)
                if self.right_image_original is None:
                    raise Exception("No se pudo cargar la imagen.")

                # Process image with recoloring (heatmap)
                self.right_image_processed = procesar_imagen(
                    ruta_archivo, None, recolor=True, foot_side="right"
                )

                # Convert to QPixmap and display on the right side
                pixmap = convertir_cv_qt(self.right_image_processed)
                self.display_right_image(pixmap)

                # Check if both images are loaded to enable 'Generar Reporte' button
                if self.left_image_original is not None and self.right_image_original is not None:
                    self.boton_generar_reporte.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo procesar la imagen.\n{str(e)}")

    def escanear_imagen_izquierda(self):
        """
        Scan the left foot image using the scanning functionality.
        """
        try:
            # Scan the image using scan_image function
            self.left_image_original = scan_image()
            if self.left_image_original is None:
                raise Exception("No se pudo escanear la imagen.")

            # Rotate the image 180 degrees if necessary
            self.left_image_original = cv2.rotate(self.left_image_original, cv2.ROTATE_180)

            # Process the image with recoloring (heatmap)
            self.left_image_processed = procesar_imagen(
                None, None, recolor=True, image=self.left_image_original, foot_side="left"
            )

            # Convert to QPixmap and display on the left side
            pixmap = convertir_cv_qt(self.left_image_processed)
            self.display_left_image(pixmap)

            # Check if both images are loaded to enable 'Generar Reporte' button
            if self.left_image_original is not None and self.right_image_original is not None:
                self.boton_generar_reporte.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo escanear o procesar la imagen.\n{str(e)}")

    def escanear_imagen_derecha(self):
        """
        Scan the right foot image using the scanning functionality.
        """
        try:
            # Scan the image using scan_image function
            self.right_image_original = scan_image()
            if self.right_image_original is None:
                raise Exception("No se pudo escanear la imagen.")

            # Rotate the image 180 degrees if necessary
            self.right_image_original = cv2.rotate(self.right_image_original, cv2.ROTATE_180)

            # Process the image with recoloring (heatmap)
            self.right_image_processed = procesar_imagen(
                None, None, recolor=True, image=self.right_image_original, foot_side="right"
            )

            # Convert to QPixmap and display on the right side
            pixmap = convertir_cv_qt(self.right_image_processed)
            self.display_right_image(pixmap)

            # Check if both images are loaded to enable 'Generar Reporte' button
            if self.left_image_original is not None and self.right_image_original is not None:
                self.boton_generar_reporte.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo escanear o procesar la imagen.\n{str(e)}")

    def display_left_image(self, pixmap):
        """
        Display the left foot image in the left QLabel.
        """
        # Scale the pixmap to fit within the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.label_imagen_izquierda.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.label_imagen_izquierda.setPixmap(scaled_pixmap)

    def display_right_image(self, pixmap):
        """
        Display the right foot image in the right QLabel.
        """
        # Scale the pixmap to fit within the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.label_imagen_derecha.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.label_imagen_derecha.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """
        Override the resizeEvent to adjust the images when the window is resized.
        """
        if self.left_image_processed is not None:
            pixmap_left = convertir_cv_qt(self.left_image_processed)
            self.display_left_image(pixmap_left)
        if self.right_image_processed is not None:
            pixmap_right = convertir_cv_qt(self.right_image_processed)
            self.display_right_image(pixmap_right)
        super().resizeEvent(event)

    def generar_reporte(self):
        """
        Generate the PDF report using the processed images and patient information.
        """
        if self.left_image_original is None or self.right_image_original is None:
            QMessageBox.warning(self, "Advertencia", "Debe cargar o escanear las imágenes de ambos pies.")
            return

        # Show input dialog to collect patient information
        dialog = PatientInfoDialog()
        if dialog.exec_() == QDialog.Accepted:
            # Get patient info
            paciente = dialog.paciente_edit.text()
            telefono = dialog.telefono_edit.text()
            longitud_pie = dialog.longitud_edit.text()
            material = dialog.material_edit.currentText()
            entrega_date = dialog.date_entrega_edit.date().toString("dd/MM/yyyy")
            fecha_escaneo = dialog.fecha_escaneo_edit.date().toString("dd/MM/yyyy")
            sucursal = dialog.sucursal_edit.currentText()
            taller = dialog.taller_edit.currentText()
            order_number = dialog.order_number_edit.text()
            observaciones = dialog.observaciones_edit.toPlainText()

            # Process images
            ruta_logotipo = os.path.join('resources', 'logo_square.png')  # Updated logo path

            # Process left images
            left_skin_image = procesar_imagen(
                None, ruta_logotipo, recolor=False, image=self.left_image_original, foot_side="left"
            )
            left_heatmap_image = procesar_imagen(
                None, ruta_logotipo, recolor=True, image=self.left_image_original, foot_side="left"
            )

            # Process right images
            right_skin_image = procesar_imagen(
                None, ruta_logotipo, recolor=False, image=self.right_image_original, foot_side="right"
            )
            right_heatmap_image = procesar_imagen(
                None, ruta_logotipo, recolor=True, image=self.right_image_original, foot_side="right"
            )

            # Generate PDF report
            try:
                generate_pdf_report(
                    paciente, telefono, order_number, sucursal, taller,
                    longitud_pie, material, entrega_date, observaciones,
                    left_skin_image, right_skin_image,
                    left_heatmap_image, right_heatmap_image,
                    self.left_image_original, self.right_image_original,
                    self.last_directory, fecha_escaneo
                )
                QMessageBox.information(self, "Éxito", "Reporte PDF generado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar el reporte PDF.\n{str(e)}")
        else:
            # User cancelled the dialog
            return

    def show_help(self):
        """
        Display the help instructions.
        """
        help_text = (
            "Instrucciones de Uso:\n\n"
            f"1. {'Cargar' if TEST_MODE else 'Escanear'} Pie Izquierdo: {'Seleccione una imagen del pie izquierdo.' if TEST_MODE else 'Escanee la imagen del pie izquierdo.'}\n"
            f"2. {'Cargar' if TEST_MODE else 'Escanear'} Pie Derecho: {'Seleccione una imagen del pie derecho.' if TEST_MODE else 'Escanee la imagen del pie derecho.'}\n"
            "3. Generar Reporte: Genere un reporte PDF con las imágenes procesadas.\n\n"
            "Presione 'Esc' para salir del modo de pantalla maximizada."
        )
        QMessageBox.information(self, "Ayuda", help_text)

    def show_about(self):
        """
        Display the about information.
        """
        about_text = (
            "Orto Flex Scanner\n\n"
            "Versión 1.0\n\n"
            "Desarrollado por Marcos Saade.\n"
            "© 2024 Todos los derechos reservados."
        )
        QMessageBox.information(self, "Acerca de", about_text)

    def load_preferences(self):
        """
        Load user preferences like window size and last directory.
        """
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_preferences(self):
        """
        Save user preferences like window size and last directory.
        """
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_directory", self.last_directory)

    def closeEvent(self, event):
        """
        Override closeEvent to save user preferences.
        """
        self.save_preferences()
        event.accept()

    def keyPressEvent(self, event):
        """
        Override keyPressEvent to allow exiting fullscreen mode with the Esc key.
        """
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        else:
            super().keyPressEvent(event)

    def nuevo(self):
        """
        Reset the application state to allow new images to be scanned.
        """
        # Reset images
        self.left_image_original = None
        self.left_image_processed = None
        self.right_image_original = None
        self.right_image_processed = None

        # Reset image labels to default background images or texts
        # Left Image
        bg_left_path = os.path.join('resources', 'bg_left.png')
        if os.path.exists(bg_left_path):
            pixmap_bg_left = QPixmap(bg_left_path)
            self.label_imagen_izquierda.setPixmap(pixmap_bg_left)
        else:
            self.label_imagen_izquierda.setText("Pie Izquierdo")
            self.label_imagen_izquierda.setFont(QFont(self.font_family, 16))
            self.label_imagen_izquierda.setStyleSheet("color: #1d3557;")

        # Right Image
        bg_right_path = os.path.join('resources', 'bg_right.png')
        if os.path.exists(bg_right_path):
            pixmap_bg_right = QPixmap(bg_right_path)
            self.label_imagen_derecha.setPixmap(pixmap_bg_right)
        else:
            self.label_imagen_derecha.setText("Pie Derecho")
            self.label_imagen_derecha.setFont(QFont(self.font_family, 16))
            self.label_imagen_derecha.setStyleSheet("color: #1d3557;")

        # Disable 'Generar Reporte' button
        self.boton_generar_reporte.setEnabled(False)


def main():
    import sys
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    # ventana.show()  # Removed because showFullScreen is called in the __init__
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# Hello
