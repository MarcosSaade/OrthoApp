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

def sanitize_filename(name):
    return re.sub(r'[^A-Za-z0-9\s_-]', '', name).strip()

def generate_pdf_report(
    paciente, telefono, order_number, sucursal, taller,
    longitud_pie, material, entrega_date, observaciones,
    left_skin_image, right_skin_image,
    left_heatmap_image, right_heatmap_image,
    left_original_image, right_original_image,
    last_directory, fecha_escaneo
):
    default_filename = "Reporte.pdf"
    if paciente and order_number:
        safe_paciente = sanitize_filename(paciente).replace(' ', '_')
        safe_order_number = sanitize_filename(order_number)
        default_filename = f"{safe_paciente}-{safe_order_number}.pdf"

    initial_path = os.path.join(last_directory, default_filename)

    opciones = QFileDialog.Options()
    ruta_archivo, _ = QFileDialog.getSaveFileName(
        None, "Guardar Reporte PDF", initial_path,
        "PDF (*.pdf)", options=opciones
    )
    if not ruta_archivo:
        raise Exception("No se seleccionó ninguna ruta para guardar el PDF.")

    if not ruta_archivo.lower().endswith('.pdf'):
        ruta_archivo += '.pdf'

    try:
        font_path = os.path.join('resources', 'Roboto-Regular.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Roboto', font_path))
        else:
            print("Roboto font not found. Using default fonts.")
    except Exception as e:
        print(f"Error registering font: {e}")

    def add_background(canvas_obj, doc):
        bg_image_path = os.path.join('resources', 'background.jpeg')
        if os.path.exists(bg_image_path):
            canvas_obj.saveState()
            canvas_obj.drawImage(bg_image_path, 0, 0, width=landscape(A4)[0], height=landscape(A4)[1])
            canvas_obj.restoreState()
        else:
            print("Background image not found.")

    doc = BaseDocTemplate(ruta_archivo, pagesize=landscape(A4))
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='test', frames=frame, onPage=add_background)
    doc.addPageTemplates([template])

    elements = []

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
        except:
            return date_str

    def create_patient_info_table():
        entrega_date_formatted = format_date_spanish(entrega_date)
        fecha_escaneo_formatted = format_date_spanish(fecha_escaneo)

        patient_info_left = f"""
        <b>Paciente:</b> {paciente}<br/>
        <b>Teléfono:</b> {telefono}<br/>
        <b>Longitud del Pie:</b> {longitud_pie}<br/>
        <b>No. Orden:</b> {order_number}<br/>
        """

        patient_info_right = f"""
        <b>Sucursal:</b> {sucursal}<br/>
        <b>Taller:</b> {taller}<br/>
        <b>Fecha de Escaneo:</b> {fecha_escaneo_formatted}<br/>
        <b>Fecha de Entrega:</b> {entrega_date_formatted}<br/>
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

    elements.append(Spacer(1, 32))
    elements.append(create_patient_info_table())

    # Convert images to RLImage
    def cv_image_to_Image(cv_image, max_width, max_height):
        is_success, buffer = cv2.imencode(".png", cv_image)
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

    def resize_image_to_fixed_size(cv_image, target_width=1100, target_height=1600):
        resized_image = cv2.resize(cv_image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        return resized_image

    left_original_resized = resize_image_to_fixed_size(left_original_image, 1100, 1600)
    right_original_resized = resize_image_to_fixed_size(right_original_image, 1100, 1600)

    left_original_flipped = cv2.flip(left_original_resized, 1)
    right_original_flipped = cv2.flip(right_original_resized, 1)

    def cv_image_to_rl_image_original(cv_image, dpi=300):
        height_px, width_px = cv_image.shape[:2]
        width_pt = (width_px / dpi) * 72
        height_pt = (height_px / dpi) * 72
        is_success, buffer = cv2.imencode(".png", cv_image)
        if not is_success:
            raise Exception("No se pudo convertir la imagen.")
        image_stream = BytesIO(buffer)
        img = RLImage(image_stream, width=width_pt, height=height_pt)
        return img

    left_original_rl = cv_image_to_rl_image_original(left_original_flipped, dpi=300)
    right_original_rl = cv_image_to_rl_image_original(right_original_flipped, dpi=300)

    def ensure_image_fits(img, max_width, max_height):
        if img.drawWidth > max_width or img.drawHeight > max_height:
            aspect = img.drawHeight / float(img.drawWidth)
            if img.drawWidth > max_width:
                img.drawWidth = max_width
                img.drawHeight = max_width * aspect
            if img.drawHeight > max_height:
                img.drawHeight = max_height
                img.drawWidth = max_height / aspect
        return img

    max_image_width = (doc.width - 6 * cm) / 4
    max_image_height = doc.height / 2

    # Convert heatmap images to RLImage
    left_heatmap_img = cv_image_to_Image(left_heatmap_image, max_image_width, max_image_height)
    right_heatmap_img = cv_image_to_Image(right_heatmap_image, max_image_width, max_image_height)

    # Adjust sizing to fit all four images in one row:
    small_space_between_elements = 0.5 * cm
    large_space_between_pairs = 2 * cm
    adjusted_image_width = (doc.width - (2 * small_space_between_elements) - large_space_between_pairs) / 4

    # Adjust original images to same width
    def adjust_image_size(img, new_width):
        aspect = img.drawHeight / float(img.drawWidth)
        img.drawWidth = new_width
        img.drawHeight = new_width * aspect
        return img

    left_original_rl = ensure_image_fits(left_original_rl, adjusted_image_width, max_image_height)
    right_original_rl = ensure_image_fits(right_original_rl, adjusted_image_width, max_image_height)

    left_original_rl = adjust_image_size(left_original_rl, adjusted_image_width)
    right_original_rl = adjust_image_size(right_original_rl, adjusted_image_width)
    left_heatmap_img = adjust_image_size(left_heatmap_img, adjusted_image_width)
    right_heatmap_img = adjust_image_size(right_heatmap_img, adjusted_image_width)

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

    elements.append(table_images)

    if observaciones.strip():
        elements.append(Spacer(1, 4))

        observaciones_heading = Paragraph("<b>Observaciones:</b>", normal_style)
        elements.append(observaciones_heading)

        observaciones_content = Paragraph(observaciones, normal_style)
        elements.append(observaciones_content)
        elements.append(Spacer(1, 24))

    doc.build(elements)
