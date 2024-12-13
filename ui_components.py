# ui_components.py
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QDateEdit, QComboBox, QLabel, QHBoxLayout, QMessageBox, QVBoxLayout, QWidget
)
from PyQt5.QtCore import QDate, Qt
import datetime


class PatientInfoDialog(QDialog):
    def __init__(self, paciente='', telefono='', longitud_pie='', material='Pelite',
                 entrega_date='', fecha_escaneo='', sucursal='Interlomas',
                 taller='1', order_number='', observaciones=''):
        super().__init__()
        self.setWindowTitle("Información del Paciente")
        self.setFixedSize(400, 700)
        layout = QFormLayout()

        # Initialize widgets with initial data
        self.paciente_edit = QLineEdit(paciente)
        self.telefono_edit = QLineEdit(telefono)
        self.longitud_edit = QLineEdit(longitud_pie)

        self.material_edit = QComboBox()
        self.material_edit.addItems(["Pelite", "Plaztasote", "Insert", "Biomecánica", "Otro"])
        self.material_edit.setCurrentText(material if material in ["Pelite", "Plaztasote", "Insert", "Biomecánica", "Otro"] else "Pelite")

        self.custom_material_edit = QLineEdit()
        self.custom_material_edit.setPlaceholderText("Ingrese el material")
        self.custom_material_edit.setVisible(material == "Otro")

        # Connect signal to handle 'Otro' selection
        self.material_edit.currentIndexChanged.connect(self.toggle_custom_material)

        self.fecha_escaneo_edit = QDateEdit()
        if fecha_escaneo:
            fecha_escaneo_date = QDate.fromString(fecha_escaneo, "dd/MM/yyyy")
            if fecha_escaneo_date.isValid():
                self.fecha_escaneo_edit.setDate(fecha_escaneo_date)
            else:
                self.fecha_escaneo_edit.setDate(QDate.currentDate())
        else:
            self.fecha_escaneo_edit.setDate(QDate.currentDate())
        self.fecha_escaneo_edit.setCalendarPopup(True)

        self.date_entrega_edit = QDateEdit()
        if entrega_date:
            entrega_date_qdate = QDate.fromString(entrega_date, "dd/MM/yyyy")
            if entrega_date_qdate.isValid():
                self.date_entrega_edit.setDate(entrega_date_qdate)
            else:
                entrega_date = self.calculate_next_delivery_date()
                self.date_entrega_edit.setDate(QDate(entrega_date.year, entrega_date.month, entrega_date.day))
        else:
            entrega_date = self.calculate_next_delivery_date()
            self.date_entrega_edit.setDate(QDate(entrega_date.year, entrega_date.month, entrega_date.day))
        self.date_entrega_edit.setCalendarPopup(True)
        self.date_entrega_edit.setEnabled(True)

        self.sucursal_edit = QComboBox()
        self.sucursal_edit.addItems(["Del Valle", "Interlomas"])
        if sucursal in ["Interlomas", "Del Valle"]:
            self.sucursal_edit.setCurrentText(sucursal)
        else:
            self.sucursal_edit.setCurrentIndex(0)

        self.taller_edit = QComboBox()
        self.taller_edit.addItems(['1', '2', '3', '4', '5'])
        if taller in ['1', '2', '3', '4', '5']:
            self.taller_edit.setCurrentText(taller)
        else:
            self.taller_edit.setCurrentIndex(0)

        self.order_number_edit = QLineEdit(order_number)

        self.observaciones_edit = QTextEdit(observaciones)
        self.observaciones_edit.setPlaceholderText("Observaciones (opcional)")

        # Add rows to the form layout
        layout.addRow("Paciente:", self.paciente_edit)
        layout.addRow("Teléfono:", self.telefono_edit)
        layout.addRow("No. Orden:", self.order_number_edit)
        layout.addRow("Longitud del Pie:", self.longitud_edit)

        # Create a horizontal layout for Material and Custom Material
        material_layout = QHBoxLayout()
        material_layout.addWidget(self.material_edit)
        material_layout.addWidget(self.custom_material_edit)
        layout.addRow("Material:", material_layout)

        layout.addRow("Fecha de Escaneo:", self.fecha_escaneo_edit)
        layout.addRow("Fecha de Entrega:", self.date_entrega_edit)
        layout.addRow("Sucursal:", self.sucursal_edit)
        layout.addRow("Taller:", self.taller_edit)
        layout.addRow("Observaciones:", self.observaciones_edit)

        # Add dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def toggle_custom_material(self, index):
        """Show or hide the custom material input based on selection."""
        self.custom_material_edit.setVisible(self.material_edit.currentText() == "Otro")

    def accept(self):
        """Handle the accept event to validate and store material information."""
        if self.material_edit.currentText() == "Otro":
            custom_material = self.custom_material_edit.text().strip()
            if not custom_material:
                QMessageBox.warning(self, "Entrada requerida", "Por favor, ingrese el material.")
                return
            self.material_value = custom_material
        else:
            self.material_value = self.material_edit.currentText()

        self.fecha_entrega = self.date_entrega_edit.date().toPyDate()

        super().accept()

    def get_material(self):
        """Retrieve the value of material."""
        return self.material_value

    def get_fecha_entrega(self):
        """Retrieve the selected delivery date."""
        return self.fecha_entrega

    def calculate_next_delivery_date(self):
        """Calculate the promised delivery date based on current day and time."""
        now = datetime.datetime.now()
        today = now.date()
        current_weekday = now.weekday()  # Monday is 0 and Sunday is 6
        current_time = now.time()

        # Define processing times: Monday and Thursday at 12:30 pm
        processing_times = {
            0: datetime.time(12, 30),  # Monday
            3: datetime.time(12, 30),  # Thursday
        }

        # Calculate this week's Monday
        monday = today - datetime.timedelta(days=current_weekday)
        monday_datetime = datetime.datetime.combine(monday, processing_times[0])

        # Calculate this week's Thursday
        thursday = monday + datetime.timedelta(days=3)
        thursday_datetime = datetime.datetime.combine(thursday, processing_times[3])

        if now < monday_datetime:
            # Processing this Monday
            processing_datetime = monday_datetime
            delivery_date = monday + datetime.timedelta(days=3)  # Thursday same week
        elif monday_datetime <= now < thursday_datetime:
            # Processing this Thursday
            processing_datetime = thursday_datetime
            delivery_date = thursday + datetime.timedelta(days=4)  # Next Monday
        else:
            # Processing next Monday
            next_monday = monday + datetime.timedelta(days=7)
            processing_datetime = datetime.datetime.combine(next_monday, processing_times[0])
            delivery_date = next_monday + datetime.timedelta(days=3)  # Thursday next week

        # Promised date to client is delivery_date +1 day
        delivery_promise_date = delivery_date + datetime.timedelta(days=1)

        return delivery_promise_date


class ConfirmationDialog(QDialog):
    def __init__(self, paciente, telefono, longitud_pie, material, entrega_date,
                 fecha_escaneo, sucursal, taller, order_number, observaciones):
        super().__init__()
        self.setWindowTitle("Confirmación de Información")
        self.setFixedSize(500, 600)
        layout = QVBoxLayout()

        # Display patient information
        info_labels = [
            f"<b>Paciente:</b> {paciente}",
            f"<b>Teléfono:</b> {telefono}",
            f"<b>Longitud del Pie:</b> {longitud_pie}",
            f"<b>Material:</b> {material}",
            f"<b>Fecha de Entrega:</b> {entrega_date}",
            f"<b>Fecha de Escaneo:</b> {fecha_escaneo}",
            f"<b>Sucursal:</b> {sucursal}",
            f"<b>Taller:</b> {taller}",
            f"<b>No. Orden:</b> {order_number}",
            f"<b>Observaciones:</b> {observaciones if observaciones.strip() else 'N/A'}"
        ]

        for info in info_labels:
            label = QLabel(info)
            label.setWordWrap(True)
            layout.addWidget(label)

        # Add dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Confirmar y Generar Reporte")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar y Editar Información")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
