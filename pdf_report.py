# pdf_report.py
import os
import cv2
import re
from io import BytesIO
from reportlab.platypus import (
    Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from PyQt5.QtWidgets import QFileDialog
import datetime


def sanitize_filename(name):
    # Remove any character that is not alphanumeric, space, hyphen, or underscore
    return re.sub(r'[^A-Za-z0-9\s_-]', '', name).strip()


def generate_pdf_report(
    paciente, telefono, order_number, sucursal, taller,
    longitud_pie, material, entrega_date, observaciones,
    left_skin_image, right_skin_image,
    left_heatmap_image, right_heatmap_image,
    left_original_image, right_original_image,
    last_directory, fecha_escaneo
):
    # Build the default filename if paciente and order_number are provided
    default_filename = "Reporte.pdf"
    if paciente and order_number:
        safe_paciente = sanitize_filename(paciente).replace(' ', '_')
        safe_order_number = sanitize_filename(order_number)
        default_filename = f"{safe_paciente}-{safe_order_number}.pdf"

    initial_path = os.path.join(last_directory, default_filename)

    # Ask the user where to save the PDF
    opciones = QFileDialog.Options()
    ruta_archivo, _ = QFileDialog.getSaveFileName(
        None, "Guardar Reporte PDF", initial_path,
        "PDF (*.pdf)", options=opciones
    )
    if not ruta_archivo:
        raise Exception("No se seleccionó ninguna ruta para guardar el PDF.")

    # Ensure the file has a .pdf extension
    if not ruta_archivo.lower().endswith('.pdf'):
        ruta_archivo += '.pdf'

    # Register Roboto font
    try:
        font_path = os.path.join('resources', 'Roboto-Regular.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Roboto', font_path))
        else:
            print("Roboto font not found. Using default fonts.")
    except Exception as e:
        print(f"Error registering font: {e}")

    # Create a custom document template to add background image
    def add_background(canvas_obj, doc):
        # Draw the background image
        bg_image_path = os.path.join('resources', 'background.jpeg')  # Background image path
        if os.path.exists(bg_image_path):
            canvas_obj.saveState()
            canvas_obj.drawImage(bg_image_path, 0, 0, width=landscape(A4)[0], height=landscape(A4)[1])
            canvas_obj.restoreState()
        else:
            print("Background image not found.")

    # Create the document
    doc = BaseDocTemplate(ruta_archivo, pagesize=landscape(A4))

    # Create a Frame for content
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')

    # Add PageTemplate with onPage function
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

    # Helper function to translate weekday and month to Spanish
    def format_date_spanish(date_str):
        """
        Formats a date string from 'dd/MM/yyyy' to 'Día de la semana número mes año'.
        Example: '21/12/2024' -> 'Martes 21 de Diciembre de 2024'
        """
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
            print(f"Error formatting date: {e}")
            return date_str  # Fallback to original string

    # Function to create patient info table
    def create_patient_info_table():
        # Format dates
        entrega_date_formatted = format_date_spanish(entrega_date)
        fecha_escaneo_formatted = format_date_spanish(fecha_escaneo)

        patient_info_left = f"""
        <b>Sucursal:</b> {sucursal}<br/>
        <b>Taller:</b> {taller}<br/>
        <b>Fecha de Escaneo:</b> {fecha_escaneo_formatted}<br/>
        <b>Fecha de Entrega:</b> {entrega_date_formatted}<br/>
        """

        patient_info_right = f"""
        <b>Paciente:</b> {paciente}<br/>
        <b>Teléfono:</b> {telefono}<br/>
        <b>Longitud del Pie:</b> {longitud_pie}<br/>
        <b>No. Orden:</b> {order_number}<br/>
        """

        data_patient_info = [
            [Paragraph(patient_info_left, normal_style),
             Paragraph(patient_info_right, normal_style)]
        ]

        # Adjust column widths
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

    # Add patient information and images on the first page
    elements.append(Spacer(1, 24))
    elements.append(create_patient_info_table())
    elements.append(Spacer(1, 36))

    # Function to convert OpenCV image to ReportLab Image with scaling (First Page)
    def cv_image_to_Image(cv_image, max_width, max_height):
        # Encode image to PNG in memory
        is_success, buffer = cv2.imencode(".png", cv_image)
        if not is_success:
            raise Exception("No se pudo convertir la imagen.")
        image_stream = BytesIO(buffer)
        img = RLImage(image_stream)
        # Calculate aspect ratio scaling
        img_width, img_height = img.wrap(0, 0)
        aspect = img_height / float(img_width)
        if img_width > max_width:
            img.drawWidth = max_width
            img.drawHeight = max_width * aspect
        if img.drawHeight > max_height:
            img.drawHeight = max_height
            img.drawWidth = max_height / aspect
        return img

    # Define maximum image sizes for the first page
    max_image_width = (doc.width - 6 * cm) / 4  # Adjusted to accommodate spacing and borders
    max_image_height = doc.height / 2

    # Process images for the first page
    left_skin_img = cv_image_to_Image(left_skin_image, max_image_width, max_image_height)
    right_skin_img = cv_image_to_Image(right_skin_image, max_image_width, max_image_height)
    left_heatmap_img = cv_image_to_Image(left_heatmap_image, max_image_width, max_image_height)
    right_heatmap_img = cv_image_to_Image(right_heatmap_image, max_image_width, max_image_height)

    # Define spacing
    small_space_between_elements = 0.5 * cm  # Space between images within a pair
    large_space_between_pairs = 2 * cm        # Space between the two pairs

    # Calculate adjusted image width to fit within the page considering spacings
    adjusted_image_width = (doc.width - (2 * small_space_between_elements) - large_space_between_pairs) / 4

    # Reprocess images with adjusted width while maintaining aspect ratio
    def adjust_image_size(img, new_width):
        """
        Adjusts the image size to the new_width while maintaining aspect ratio.
        """
        aspect = img.drawHeight / float(img.drawWidth)
        img.drawWidth = new_width
        img.drawHeight = new_width * aspect
        return img

    left_skin_img = adjust_image_size(left_skin_img, adjusted_image_width)
    right_skin_img = adjust_image_size(right_skin_img, adjusted_image_width)
    left_heatmap_img = adjust_image_size(left_heatmap_img, adjusted_image_width)
    right_heatmap_img = adjust_image_size(right_heatmap_img, adjusted_image_width)

    # Create data for the table with spacing between images
    data_images = [
        [left_skin_img, Spacer(1, small_space_between_elements), right_skin_img,
         Spacer(1, large_space_between_pairs), left_heatmap_img, Spacer(1, small_space_between_elements), right_heatmap_img]
    ]

    # Define column widths: image, small spacer, image, large spacer, image, small spacer, image
    colWidths = [
        adjusted_image_width,               # left_skin_img
        small_space_between_elements,       # Spacer between left and right skin images
        adjusted_image_width,               # right_skin_img
        large_space_between_pairs,          # Spacer between skin and heatmap images
        adjusted_image_width,               # left_heatmap_img
        small_space_between_elements,       # Spacer between left and right heatmap images
        adjusted_image_width                # right_heatmap_img
    ]

    # Create the table with the specified column widths
    table_images = Table(data_images, colWidths=colWidths, hAlign='CENTER')

    # Define table styles
    table_images.setStyle(TableStyle([
        # Add a black border around each individual image
        ('BOX', (0, 0), (0, 0), 1, colors.black),  # Border around left_skin_img
        ('BOX', (2, 0), (2, 0), 1, colors.black),  # Border around right_skin_img
        ('BOX', (4, 0), (4, 0), 1, colors.black),  # Border around left_heatmap_img
        ('BOX', (6, 0), (6, 0), 1, colors.black),  # Border around right_heatmap_img

        # Center align the images
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Remove borders from spacer columns
        ('LINEBELOW', (1, 0), (1, 0), 0, colors.white),
        ('LINEBELOW', (3, 0), (3, 0), 0, colors.white),
        ('LINEBELOW', (5, 0), (5, 0), 0, colors.white),

        # Adjust padding to control spacing around images
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    # Add the images table to the elements
    elements.append(table_images)
    elements.append(Spacer(1, 24))

    # Add second page
    elements.append(PageBreak())

    # Add Spacer to vertically center the content on the second page
    elements.append(Spacer(1, 2 * inch))  # Adjust the spacer height as needed

    # --- Begin Modifications for Original Images ---

    # Step 1: Resize Original Images to 1100x1600 Pixels
    def resize_image_to_fixed_size(cv_image, target_width=1100, target_height=1600):
        """
        Resizes the given OpenCV image to the target dimensions.

        :param cv_image: OpenCV image (numpy array)
        :param target_width: Desired width in pixels
        :param target_height: Desired height in pixels
        :return: Resized OpenCV image
        """
        resized_image = cv2.resize(cv_image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        return resized_image

    # Resize the original images
    left_original_resized = resize_image_to_fixed_size(left_original_image, 1100, 1600)
    right_original_resized = resize_image_to_fixed_size(right_original_image, 1100, 1600)

    # Flip the original images horizontally
    left_original_flipped = cv2.flip(left_original_resized, 1)   # 1 denotes horizontal flip
    right_original_flipped = cv2.flip(right_original_resized, 1)

    # Step 2: Convert Resized Images to ReportLab Image Objects Without Additional Scaling
    def cv_image_to_rl_image_original(cv_image, dpi=300):
        """
        Converts an OpenCV image to a ReportLab Image with exact pixel dimensions.

        :param cv_image: OpenCV image (numpy array)
        :param dpi: Dots per inch for scaling (default: 300)
        :return: ReportLab Image object
        """
        # Get image dimensions in pixels
        height_px, width_px = cv_image.shape[:2]

        # Calculate size in points
        width_pt = (width_px / dpi) * 72
        height_pt = (height_px / dpi) * 72

        # Encode image to PNG in memory
        is_success, buffer = cv2.imencode(".png", cv_image)
        if not is_success:
            raise Exception("No se pudo convertir la imagen.")
        image_stream = BytesIO(buffer)

        # Create ReportLab Image with exact dimensions
        img = RLImage(image_stream, width=width_pt, height=height_pt)
        return img

    # Define DPI for original images (Adjust if necessary)
    ORIGINAL_IMAGE_DPI = 300

    # Convert resized and flipped original images to ReportLab Images
    left_original_rl = cv_image_to_rl_image_original(left_original_flipped, dpi=ORIGINAL_IMAGE_DPI)
    right_original_rl = cv_image_to_rl_image_original(right_original_flipped, dpi=ORIGINAL_IMAGE_DPI)

    # Optional: Ensure images fit within the page (if needed)
    def ensure_image_fits(img, max_width, max_height):
        """
        Adjusts the image size if it exceeds the maximum allowed dimensions.

        :param img: ReportLab Image object
        :param max_width: Maximum width in points
        :param max_height: Maximum height in points
        :return: Adjusted ReportLab Image object
        """
        if img.drawWidth > max_width or img.drawHeight > max_height:
            aspect = img.drawHeight / float(img.drawWidth)
            if img.drawWidth > max_width:
                img.drawWidth = max_width
                img.drawHeight = max_width * aspect
            if img.drawHeight > max_height:
                img.drawHeight = max_height
                img.drawWidth = max_height / aspect
        return img

    # Define maximum dimensions for original images (e.g., page width minus margins)
    max_orig_width = (doc.width / 2) - 2 * cm  # Adjusted for individual boxes
    max_orig_height = (doc.height / 2) - 2 * cm  # Adjusted for individual boxes

    # Ensure original images fit within the page
    left_original_rl = ensure_image_fits(left_original_rl, max_orig_width, max_orig_height)
    right_original_rl = ensure_image_fits(right_original_rl, max_orig_width, max_orig_height)

    # Step 3: Create a Table for the Original Images on the Second Page with Separation
    # Introduce a large spacer between the two images
    data_original = [
        [left_original_rl, Spacer(1, large_space_between_pairs), right_original_rl]
    ]

    # Define column widths: image, large spacer, image
    colWidths_orig = [
        max_orig_width,                    # left_original_rl
        large_space_between_pairs,         # Spacer between original images
        max_orig_width                     # right_original_rl
    ]

    table_original = Table(data_original, colWidths=colWidths_orig, hAlign='CENTER')

    table_original.setStyle(TableStyle([
        # Add a black border around each individual image
        ('BOX', (0, 0), (0, 0), 1, colors.black),  # Border around left_original_rl
        ('BOX', (2, 0), (2, 0), 1, colors.black),  # Border around right_original_rl

        # Center align the images
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Remove borders from spacer columns
        ('LINEBELOW', (1, 0), (1, 0), 0, colors.white),

        # Adjust padding to control spacing around images
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(table_original)

    # --- End Modifications for Original Images ---

    # Now, add Observaciones below the images on the second page
    if observaciones.strip():
        # Add a separator line
        elements.append(Spacer(1, 8))  # Increased spacer for better separation
        separator = Table([[Paragraph('<hr/>', normal_style)]], colWidths=[doc.width])
        elements.append(separator)
        elements.append(Spacer(1, 12))

        # Add Observaciones heading
        observaciones_heading = Paragraph("<b>Observaciones:</b>", normal_style)
        elements.append(observaciones_heading)

        # Add Observaciones content
        observaciones_content = Paragraph(observaciones, normal_style)
        elements.append(observaciones_content)
        elements.append(Spacer(1, 24))

    # Build the PDF
    doc.build(elements)
