# ui_components.py
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QDateEdit, QComboBox
)
from PyQt5.QtCore import QDate
import datetime


class PatientInfoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Información del Paciente")
        self.setFixedSize(400, 600)  # Increased size to accommodate more fields
        layout = QFormLayout()

        # Paciente
        self.paciente_edit = QLineEdit()

        # Teléfono
        self.telefono_edit = QLineEdit()

        # Longitud del Pie
        self.longitud_edit = QLineEdit()

        # Material
        self.material_edit = QComboBox()
        self.material_edit.addItems(["Pelite", "Plaztasote", "Insert", "Biomecánica", "Otro"])  # Added "Otro"
        self.material_edit.setCurrentText("Pelite")  # Set "Pelite" as the default selection

        # Fecha de Escaneo
        self.fecha_escaneo_edit = QDateEdit()
        self.fecha_escaneo_edit.setDate(QDate.currentDate())
        self.fecha_escaneo_edit.setCalendarPopup(True)

        # Fecha de Entrega
        self.date_entrega_edit = QDateEdit()
        entrega_date = self.calculate_next_delivery_date()
        self.date_entrega_edit.setDate(QDate(entrega_date.year, entrega_date.month, entrega_date.day))
        self.date_entrega_edit.setCalendarPopup(True)

        # Sucursal (dropdown menu)
        self.sucursal_edit = QComboBox()
        self.sucursal_edit.addItems(["Interlomas", "Del Valle"])
        self.sucursal_edit.setCurrentIndex(0)  # Default to 'Interlomas'

        # Taller (dropdown menu with options 1 to 5)
        self.taller_edit = QComboBox()
        self.taller_edit.addItems(['1', '2', '3', '4', '5'])
        self.taller_edit.setCurrentIndex(0)  # Default to '1'

        # No. Orden
        self.order_number_edit = QLineEdit()

        # Observaciones
        self.observaciones_edit = QTextEdit()
        self.observaciones_edit.setPlaceholderText("Observaciones (opcional)")

        # Add fields to the form layout in the specified order
        layout.addRow("Paciente:", self.paciente_edit)
        layout.addRow("Teléfono:", self.telefono_edit)
        layout.addRow("Longitud del Pie:", self.longitud_edit)
        layout.addRow("Material:", self.material_edit)
        layout.addRow("Fecha de Escaneo:", self.fecha_escaneo_edit)
        layout.addRow("Fecha de Entrega:", self.date_entrega_edit)
        layout.addRow("Sucursal:", self.sucursal_edit)
        layout.addRow("Taller:", self.taller_edit)
        layout.addRow("No. Orden:", self.order_number_edit)
        layout.addRow("Observaciones:", self.observaciones_edit)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def calculate_next_delivery_date(self):
        today = datetime.date.today()
        target_weekday = 1  # Tuesday (Monday is 0)

        days_ahead = (target_weekday - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7

        entrega_date = today + datetime.timedelta(days=days_ahead)
        return entrega_date
