# ui_components.py
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QDateEdit, QComboBox, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
import datetime

class PatientInfoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Información del Paciente")
        self.setFixedSize(400, 700)
        layout = QFormLayout()

        # Initialize widgets
        self.paciente_edit = QLineEdit()
        self.telefono_edit = QLineEdit()
        self.longitud_edit = QLineEdit()

        self.material_edit = QComboBox()
        self.material_edit.addItems(["Pelite", "Plaztasote", "Insert", "Biomecánica", "Otro"])
        self.material_edit.setCurrentText("Pelite")

        self.custom_material_edit = QLineEdit()
        self.custom_material_edit.setPlaceholderText("Ingrese el material")
        self.custom_material_edit.setVisible(False)  # Hidden by default

        # Connect signal to handle 'Otro' selection
        self.material_edit.currentIndexChanged.connect(self.toggle_custom_material)

        self.fecha_escaneo_edit = QDateEdit()
        self.fecha_escaneo_edit.setDate(QDate.currentDate())
        self.fecha_escaneo_edit.setCalendarPopup(True)

        self.date_entrega_edit = QDateEdit()
        entrega_date = self.calculate_next_delivery_date()
        self.date_entrega_edit.setDate(QDate(entrega_date.year, entrega_date.month, entrega_date.day))
        self.date_entrega_edit.setCalendarPopup(True)
        self.date_entrega_edit.setEnabled(True)

        self.sucursal_edit = QComboBox()
        self.sucursal_edit.addItems(["Interlomas", "Del Valle"])
        self.sucursal_edit.setCurrentIndex(0)

        self.taller_edit = QComboBox()
        self.taller_edit.addItems(['1', '2', '3', '4', '5'])
        self.taller_edit.setCurrentIndex(0)

        self.order_number_edit = QLineEdit()

        self.observaciones_edit = QTextEdit()
        self.observaciones_edit.setPlaceholderText("Observaciones (opcional)")

        # Add rows to the form layout
        layout.addRow("Paciente:", self.paciente_edit)
        layout.addRow("Teléfono:", self.telefono_edit)
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
        layout.addRow("No. Orden:", self.order_number_edit)
        layout.addRow("Observaciones:", self.observaciones_edit)

        # Add dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def toggle_custom_material(self, index):
        """Show or hide the custom material input based on selection."""
        if self.material_edit.currentText() == "Otro":
            self.custom_material_edit.setVisible(True)
        else:
            self.custom_material_edit.setVisible(False)

    def accept(self):
        """Override accept to handle custom material input."""
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
        now = datetime.datetime.now()
        today = now.date()
        current_weekday = now.weekday()
        current_time = now.time()
        cutoff_time = datetime.time(12, 30)

        # Determine the effective day based on current day and time
        effective_day = today
        if current_weekday == 0 and current_time < cutoff_time:
            # Monday before 12:30 PM, treat as Sunday
            effective_day = today - datetime.timedelta(days=1)
        elif current_weekday == 3 and current_time < cutoff_time:
            # Thursday before 12:30 PM, treat as Wednesday
            effective_day = today - datetime.timedelta(days=1)
        else:
            # Otherwise, use today
            effective_day = today

        effective_weekday = effective_day.weekday()

        # Determine target weekday based on effective day
        if effective_weekday in [0, 1, 2]:
            target_weekday = 1 
        else:
            target_weekday = 4

        # Calculate the number of days ahead
        days_ahead = target_weekday - effective_weekday
        if days_ahead <= 0:
            days_ahead += 7

        entrega_date = effective_day + datetime.timedelta(days=days_ahead)
        return entrega_date
