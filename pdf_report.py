# pdf_report.py
import os
import cv2
import re
from io import BytesIO
from reportlab.platypus import Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from PyQt5.QtWidgets import QFileDialog
import datetime
import numpy as np

def sanitize_filename(name):
    return re.sub(r'[^A-Za-z0-9\s_-]', '', name).strip()

def format_date_spanish(date_str):
    day_names = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo"
    }
    month_names = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }
    try:
        day, month, year = map(int, date_str.split('/'))
        date_obj = datetime.date(year, month, day)
        weekday = day_names[date_obj.weekday()]
        month_name = month_names[month]
        return f"{weekday} {day} de {month_name} de {year}"
    except Exception as e:
        print(f"Error al formatear la fecha: {e}")
        return date_str

# Global patient info table function.
# (Now accepts 'longitud_pie' and an extra parameter 'bold_font' to format field labels.)
def create_patient_info_table(paciente, telefono, order_number, sucursal,
                              material, taller, fecha_escaneo_formatted,
                              entrega_date_formatted, longitud_pie,
                              normal_style, doc, bold_font):
    patient_info_left = f"""
    <font name="{bold_font}">Paciente:</font> {paciente}<br/>
    <font name="{bold_font}">Teléfono:</font> {telefono}<br/>
    <font name="{bold_font}">Longitud del Pie:</font> {longitud_pie}<br/>
    <font name="{bold_font}">No. Orden:</font> {order_number}<br/>
    <font name="{bold_font}">Sucursal:</font> {sucursal}<br/>
    """
    patient_info_right = f"""
    <font name="{bold_font}">Material:</font> {material}<br/>
    <font name="{bold_font}">Taller:</font> {taller}<br/>
    <font name="{bold_font}">Fecha de Escaneo:</font> {fecha_escaneo_formatted}<br/>
    <font name="{bold_font}">Fecha de Entrega:</font> {entrega_date_formatted}<br/>
    """
    data_patient_info = [
        [Paragraph(patient_info_left, normal_style),
         Paragraph(patient_info_right, normal_style)]
    ]
    table_patient_info = Table(
        data_patient_info,
        colWidths=[doc.width * 0.5, doc.width * 0.5]
    )
    table_patient_info.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return table_patient_info

def generate_pdf_report(
    paciente, telefono, order_number, sucursal, taller,
    longitud_pie, material, observaciones,
    left_skin_image, right_skin_image,
    left_heatmap_image, right_heatmap_image,
    left_original_image, right_original_image,
    last_pdf_directory, fecha_escaneo,
    fecha_entrega,
    no_feet_report=False
):
    # Validate input types for directories and dates
    if not isinstance(last_pdf_directory, (str, bytes, os.PathLike)):
        raise TypeError("El parámetro 'last_pdf_directory' debe ser una cadena que representa una ruta válida.")
    if not isinstance(fecha_entrega, (datetime.date, datetime.datetime, str)):
        raise TypeError("El parámetro 'fecha_entrega' debe ser una cadena con formato 'dd/mm/yyyy' o un objeto datetime.")
    if not isinstance(fecha_escaneo, (datetime.date, datetime.datetime, str)):
        raise TypeError("El parámetro 'fecha_escaneo' debe ser una cadena con formato 'dd/mm/yyyy' o un objeto datetime.")

    # Process dates
    if isinstance(fecha_entrega, (datetime.date, datetime.datetime)):
        entrega_date_str = fecha_entrega.strftime("%d/%m/%Y")
    elif isinstance(fecha_entrega, str):
        entrega_date_str = fecha_entrega
    else:
        raise ValueError("fecha_entrega debe ser una cadena con formato 'dd/mm/yyyy' o un objeto datetime.")
    entrega_date_formatted = format_date_spanish(entrega_date_str)

    if isinstance(fecha_escaneo, (datetime.date, datetime.datetime)):
        fecha_escaneo_str = fecha_escaneo.strftime("%d/%m/%Y")
    elif isinstance(fecha_escaneo, str):
        fecha_escaneo_str = fecha_escaneo
    else:
        raise ValueError("fecha_escaneo debe ser una cadena con formato 'dd/mm/yyyy' o un objeto datetime.")
    fecha_escaneo_formatted = format_date_spanish(fecha_escaneo_str)

    # Generate safe file name. If order number is empty, default to 52763.
    safe_paciente = sanitize_filename(paciente).replace(' ', '_') if paciente.strip() else "Paciente"
    if not order_number.strip():
        order_number = "52763"
    safe_order_number = sanitize_filename(order_number)
    default_filename = f"{safe_paciente}-{safe_order_number}.pdf"
    initial_path = os.path.join(last_pdf_directory, default_filename)

    opciones = QFileDialog.Options()
    ruta_archivo, _ = QFileDialog.getSaveFileName(
        None, "Guardar Reporte PDF", initial_path,
        "PDF (*.pdf)", options=opciones
    )
    if not ruta_archivo:
        raise Exception("No se seleccionó ninguna ruta para guardar el PDF.")
    if not ruta_archivo.lower().endswith('.pdf'):
        ruta_archivo += '.pdf'

    # Register fonts. Try to register both Roboto (regular) and Roboto-Bold.
    try:
        font_path = os.path.join('resources', 'Roboto-Regular.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Roboto', font_path))
        else:
            print("Roboto font not found. Using default fonts.")
        bold_font_path = os.path.join('resources', 'Roboto-Bold.ttf')
        if os.path.exists(bold_font_path):
            pdfmetrics.registerFont(TTFont('Roboto-Bold', bold_font_path))
        else:
            print("Roboto-Bold font not found. Bold tags might not render as expected.")
    except Exception as e:
        print(f"Error al registrar la fuente: {e}")

    styles = getSampleStyleSheet()
    if 'Roboto' in pdfmetrics.getRegisteredFontNames():
        title_style = ParagraphStyle('Title', parent=styles['Title'], fontName='Roboto')
        normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Roboto', fontSize=12)
        heading_style = ParagraphStyle(
            'Heading', parent=styles['Heading1'], fontName='Roboto',
            fontSize=14, leading=16, spaceAfter=12, alignment=1
        )
    else:
        title_style = styles['Title']
        normal_style = styles['Normal']
        heading_style = ParagraphStyle(
            name='Heading', fontSize=14, leading=16, spaceAfter=12,
            alignment=1, fontName='Helvetica-Bold'
        )

    # Determine which bold font to use for field labels.
    if 'Roboto-Bold' in pdfmetrics.getRegisteredFontNames():
        bold_font = "Roboto-Bold"
    else:
        bold_font = "Helvetica-Bold"

    if no_feet_report:
        PAGE_WIDTH = 1587
        PAGE_HEIGHT = 2245
        # Set margins: 2cm left/right, 2cm top, and 0 for bottom
        doc = BaseDocTemplate(
            ruta_archivo, 
            pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=0
        )
        
        def add_no_feet_background(canvas_obj, doc):
            bg_image_path = os.path.join('resources', 'bg_no_feet.jpg')
            if os.path.exists(bg_image_path):
                canvas_obj.saveState()
                canvas_obj.drawImage(bg_image_path, 0, 0, 
                                width=PAGE_WIDTH, height=PAGE_HEIGHT)
                canvas_obj.restoreState()

        # Frame covering bottom half of the page
        frame = Frame(
            doc.leftMargin,  # 2cm left margin
            0,  # Start at bottom of page
            doc.width,  # Calculated width
            PAGE_HEIGHT/2,  # Half page height
            id='bottom'
        )
        
        template = PageTemplate(id='no_feet', frames=frame, 
                            onPage=add_no_feet_background)
        doc.addPageTemplates([template])

        # Increase base font size for no-feet report
        if 'Roboto' in pdfmetrics.getRegisteredFontNames():
            normal_style = ParagraphStyle('Normal', 
                parent=styles['Normal'], 
                fontName='Roboto', 
                fontSize=32,
                leading=80  # Add line spacing
            )
        else:
            normal_style = ParagraphStyle(
                name='Normal', 
                fontSize=32,
                leading=80,
                fontName='Helvetica'
            )

        elements = []
        elements.append(Spacer(1, 72))  # Increased top spacing
        
        # Use the global create_patient_info_table (which now includes 'longitud_pie' and uses bold_font)
        elements.append(create_patient_info_table(
            paciente, telefono, order_number, sucursal,
            material, taller, fecha_escaneo_formatted, entrega_date_formatted,
            longitud_pie, normal_style, doc, bold_font
        ))
        
        if observaciones.strip():
            observaciones_style = ParagraphStyle(
                'Observaciones', 
                parent=normal_style,
                spaceBefore=0,
                spaceAfter=0
            )
            elements.append(Paragraph(f"<font name='{bold_font}'>Observaciones:</font>", observaciones_style))
            elements.append(Paragraph(observaciones, observaciones_style))
        
        doc.build(elements)
        print("Reporte PDF generado exitosamente (sin imágenes de pies).")
        return ruta_archivo
    else:
        # Normal report layout (with images)
        doc = BaseDocTemplate(ruta_archivo, pagesize=landscape(A4))
        def add_background(canvas_obj, doc):
            bg_image_path = os.path.join('resources', 'background.jpeg')
            if os.path.exists(bg_image_path):
                canvas_obj.saveState()
                try:
                    canvas_obj.drawImage(bg_image_path, 0, 0, width=landscape(A4)[0], height=landscape(A4)[1])
                except Exception as e:
                    print(f"Error al dibujar la imagen de fondo: {e}")
                canvas_obj.restoreState()
            else:
                print("Imagen de fondo no encontrada.")
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='test', frames=frame, onPage=add_background)
        doc.addPageTemplates([template])
        elements = []
        elements.append(Spacer(1, 24))
        # Use the global create_patient_info_table (with bold field labels)
        elements.append(create_patient_info_table(
            paciente, telefono, order_number, sucursal,
            material, taller, fecha_escaneo_formatted, entrega_date_formatted,
            longitud_pie, normal_style, doc, bold_font
        ))
        
        # Helper to overlay a logo and convert a cv image to an RL image (used for heatmaps)
        def cv_image_to_Image_with_logo(cv_image, logo_path, position, max_width, max_height):
            if not isinstance(cv_image, np.ndarray):
                raise TypeError("cv_image debe ser un objeto ndarray de OpenCV.")
            def overlay_logo(imagen, logo_path, position='bottom_right', scale=0.2):
                if not os.path.exists(logo_path):
                    print(f"Archivo de logo no encontrado en {logo_path}. Saltando superposición del logo.")
                    return imagen
                logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                if logo is None:
                    print(f"Fallo al cargar el logo desde {logo_path}. Saltando superposición del logo.")
                    return imagen
                h_img, w_img = imagen.shape[:2]
                h_logo, w_logo = logo.shape[:2]
                logo_width = int(w_img * scale)
                aspect_ratio = w_logo / h_logo
                logo_height = int(logo_width / aspect_ratio)
                if logo_height > h_img or logo_width > w_img:
                    return imagen
                logo_resized = cv2.resize(logo, (logo_width, logo_height), interpolation=cv2.INTER_AREA)
                if position == 'bottom_right':
                    x = w_img - logo_width - 60
                    y = h_img - logo_height
                elif position == 'bottom_left':
                    x = 60
                    y = h_img - logo_height
                else:
                    x = 10
                    y = 10
                if x < 0 or y < 0 or x + logo_width > w_img or y + logo_height > h_img:
                    return imagen
                if logo_resized.shape[2] == 4:
                    alpha_logo = logo_resized[:, :, 3] / 255.0
                    for c in range(0, 3):
                        imagen[y:y + logo_height, x:x + logo_width, c] = (
                            alpha_logo * logo_resized[:, :, c] +
                            (1 - alpha_logo) * imagen[y:y + logo_height, x:x + logo_width, c]
                        )
                else:
                    imagen[y:y + logo_height, x:x + logo_width] = logo_resized
                return imagen
            cv_image_with_logo = overlay_logo(cv_image.copy(), logo_path, position=position, scale=0.2)
            is_success, buffer = cv2.imencode(".png", cv_image_with_logo)
            if not is_success:
                raise Exception("No se pudo convertir la imagen.")
            image_stream = BytesIO(buffer)
            img = RLImage(image_stream)
            img_width, img_height = img.wrap(0, 0)
            aspect = img_height / float(img_width)
            if img_width > max_width:
                img.drawWidth = max_width
                img.drawHeight = max_width * aspect
            if img.drawHeight > max_height:
                img.drawHeight = max_height
                img.drawWidth = max_height / aspect
            return img

        small_space_between_elements = 0.5 * cm
        large_space_between_pairs = 2 * cm
        max_image_width = (doc.width - 6 * cm) / 4
        max_image_height = doc.height / 2

        logo_path = os.path.join('resources', 'logo_square.png')
        
        # --- New: Convert and flip original images horizontally ---
        def cv_image_to_rlImage(cv_image, max_width, max_height):
            if not isinstance(cv_image, np.ndarray):
                raise TypeError("cv_image debe ser un objeto ndarray de OpenCV.")
            # Flip the original image horizontally
            flipped_image = cv2.flip(cv_image, 1)
            is_success, buffer = cv2.imencode(".png", flipped_image)
            if not is_success:
                raise Exception("No se pudo convertir la imagen original.")
            image_stream = BytesIO(buffer)
            img = RLImage(image_stream)
            img_width, img_height = img.wrap(0, 0)
            aspect = img_height / float(img_width)
            if img_width > max_width:
                img.drawWidth = max_width
                img.drawHeight = max_width * aspect
            if img.drawHeight > max_height:
                img.drawHeight = max_height
                img.drawWidth = max_height / aspect
            return img

        if left_original_image is not None and isinstance(left_original_image, np.ndarray):
            left_original_rl = cv_image_to_rlImage(left_original_image, max_image_width, max_image_height)
        else:
            left_original_rl = Spacer(1, max_image_height)
        
        if right_original_image is not None and isinstance(right_original_image, np.ndarray):
            right_original_rl = cv_image_to_rlImage(right_original_image, max_image_width, max_image_height)
        else:
            right_original_rl = Spacer(1, max_image_height)
        # --- End New Section ---

        left_heatmap_img = cv_image_to_Image_with_logo(
            left_heatmap_image,
            logo_path,
            position='bottom_left',
            max_width=max_image_width,
            max_height=max_image_height
        )
        right_heatmap_img = cv_image_to_Image_with_logo(
            right_heatmap_image,
            logo_path,
            position='bottom_right',
            max_width=max_image_width,
            max_height=max_image_height
        )
        adjusted_image_width = (doc.width - (2 * small_space_between_elements) - large_space_between_pairs) / 4

        # Create images table with both original and processed (heatmap) images.
        data_images = [
            [left_original_rl, Spacer(1, small_space_between_elements), right_original_rl,
             Spacer(1, large_space_between_pairs), left_heatmap_img, Spacer(1, small_space_between_elements), right_heatmap_img]
        ]
        colWidths = [
            adjusted_image_width,
            small_space_between_elements,
            adjusted_image_width,
            large_space_between_pairs,
            adjusted_image_width,
            small_space_between_elements,
            adjusted_image_width
        ]
        table_images = Table(data_images, colWidths=colWidths, hAlign='CENTER')
        table_images.setStyle(TableStyle([
            ('BOX', (0, 0), (0, 0), 1, colors.black),
            ('BOX', (2, 0), (2, 0), 1, colors.black),
            ('BOX', (4, 0), (4, 0), 1, colors.black),
            ('BOX', (6, 0), (6, 0), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(Spacer(1, 24))
        elements.append(table_images)
        if observaciones.strip():
            elements.append(Spacer(1, 4))
            observaciones_heading = Paragraph(f"<font name='{bold_font}'>Observaciones:</font>", normal_style)
            elements.append(observaciones_heading)
            observaciones_content = Paragraph(observaciones, normal_style)
            elements.append(observaciones_content)
            elements.append(Spacer(1, 24))
        doc.build(elements)
        print("Reporte PDF generado exitosamente.")
        if material.lower() in ["biomecanica", "biomecánica"]:
            base_filename = os.path.splitext(ruta_archivo)[0]
            if left_original_image is not None and not np.all(left_original_image==255):
                left_image_path = f"{base_filename}-i.png"
                cv2.imwrite(left_image_path, left_original_image)
            if right_original_image is not None and not np.all(right_original_image==255):
                right_image_path = f"{base_filename}-d.png"
                cv2.imwrite(right_image_path, right_original_image)
        return ruta_archivo
