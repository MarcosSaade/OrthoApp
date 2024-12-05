# image_processing.py

import cv2
import numpy as np
import os

def procesar_imagen(ruta, ruta_logotipo, recolor=True, image=None, foot_side="right"):
    """
    Processes the image to remove the background, optionally apply recoloring, 
    and add specific lines (vertical, horizontal, diagonal) and red cross markers.

    Args:
        ruta (str): Path to the image to process.
        ruta_logotipo (str): Path to the logo to add.
        recolor (bool): If True, applies recoloring; if False, keeps original colors.
        image (np.ndarray): Loaded image (optional, to avoid reloading).
        foot_side (str): Indicates if the foot is 'left' or 'right'.

    Returns:
        np.ndarray: Processed image.
    """
    # Load the image
    if image is not None:
        imagen = image.copy()
    elif ruta:
        imagen = cv2.imread(ruta)
    else:
        raise ValueError("Debe proporcionar una ruta de imagen o una imagen.")

    if imagen is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {ruta}")

    # Flip the image horizontally to conserve feet orientation
    imagen = cv2.flip(imagen, 1)  # 1 indicates horizontal flipping

    # Create an elliptical mask
    height, width = imagen.shape[:2]
    mask_ellipse = np.zeros((height, width), dtype=np.uint8)
    center = (width // 2, height // 2)
    axes = (width // 3, height)
    cv2.ellipse(mask_ellipse, center, axes, 0, 0, 360, 255, -1)

    # Apply the elliptical mask to the image
    imagen = cv2.bitwise_and(imagen, imagen, mask=mask_ellipse)

    # Convert to HSV for segmentation
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)

    # Define skin color range (adjust as needed)
    lower_skin = np.array([0, 100, 100], dtype=np.uint8)
    upper_skin = np.array([140, 255, 255], dtype=np.uint8)

    # Create a mask for the foot
    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Apply Gaussian Blur to smooth the edges of the mask
    mask = cv2.GaussianBlur(mask, (7, 7), 0)

    # Clean the mask using morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=35)  # Close holes

    # Find contours to isolate the largest region (the foot)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    refined_mask = np.zeros_like(mask)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(refined_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    else:
        raise ValueError("No se encontró ninguna forma de pie en la imagen.")

    # Apply the refined mask to extract the foreground
    imagen_sin_fondo = cv2.bitwise_and(imagen, imagen, mask=refined_mask)

    if recolor:
        # Create a white background
        fondo_blanco = np.ones_like(imagen) * 255

        # Create an inverse mask for the background
        mask_inv = cv2.bitwise_not(refined_mask)

        # Extract the background where the mask is not present
        fondo = cv2.bitwise_and(fondo_blanco, fondo_blanco, mask=mask_inv)

        # Combine the foreground with the white background
        imagen_con_fondo_blanco = cv2.add(fondo, imagen_sin_fondo)

        # Convert to grayscale and normalize for the heatmap
        imagen_gris = cv2.cvtColor(imagen_con_fondo_blanco, cv2.COLOR_BGR2GRAY)
        imagen_normalizada = cv2.normalize(imagen_gris, None, 0, 255, cv2.NORM_MINMAX)

        # Apply heatmap
        heatmap = cv2.applyColorMap(imagen_normalizada, cv2.COLORMAP_JET)

        # Convert the refined mask to 3 channels to match the heatmap
        refined_mask_3ch = cv2.cvtColor(refined_mask, cv2.COLOR_GRAY2BGR)

        # Apply the refined mask to the heatmap to remove any background overflow
        heatmap_foreground = cv2.bitwise_and(heatmap, refined_mask_3ch)

        # Combine the heatmap foreground with the white background
        final_image = cv2.add(fondo, heatmap_foreground)
    else:
        # Create a white background
        fondo_blanco = np.ones_like(imagen) * 255

        # Create an inverse mask for the background
        mask_inv = cv2.bitwise_not(refined_mask)

        # Extract the background where the mask is not present
        fondo = cv2.bitwise_and(fondo_blanco, fondo_blanco, mask=mask_inv)

        # Combine the foreground with the white background
        final_image = cv2.add(fondo, imagen_sin_fondo)

    # Add lines and markers to the image, passing the foot_side parameter and largest_contour
    final_image = agregar_lineas(final_image, largest_contour, foot_side)

    # Add logo if provided
    if ruta_logotipo and os.path.exists(ruta_logotipo):
        final_image = agregar_logotipo(final_image, ruta_logotipo)

    return final_image

def agregar_lineas(imagen, foot_contour, foot_side="right"):
    """
    Adds lines and red cross markers to the image, deriving line endpoints from the foot mask.

    Args:
        imagen (np.ndarray): Input image.
        foot_contour (np.ndarray): Contour of the foot.
        foot_side (str): Indicates if the foot is 'left' or 'right'.

    Returns:
        np.ndarray: Image with the lines and markers added.
    """
    # Get image dimensions
    height, width = imagen.shape[:2]

    # Define line thickness
    line_thickness = 5
    white_color = (255, 255, 255)  # White color in BGR
    red_color = (0, 0, 255)        # Red color in BGR

    # Convert foot_contour to array of points
    contour_points = foot_contour.reshape(-1, 2)

    # Find heel point (point with maximum y-coordinate)
    heel_point = contour_points[contour_points[:, 1].argmax()]
    heel_x, heel_y = heel_point

    # Find big toe point and little toe point
    # For the big toe, find the point with the minimum y-coordinate (topmost point) and extreme x-coordinate
    # For the little toe, find the point with the minimum y-coordinate and opposite extreme x-coordinate

    # First, find the topmost points (toes area)
    top_points = contour_points[contour_points[:, 1] <= contour_points[:, 1].min() + 0.05 * height]

    if foot_side.lower() == "right":
        # For the right foot, big toe is on the left side (minimum x)
        big_toe_point = top_points[top_points[:, 0].argmin()]
        # Little toe is on the right side (maximum x)
        little_toe_point = top_points[top_points[:, 0].argmax()]
    else:
        # For the left foot, big toe is on the right side (maximum x)
        big_toe_point = top_points[top_points[:, 0].argmax()]
        # Little toe is on the left side (minimum x)
        little_toe_point = top_points[top_points[:, 0].argmin()]

    thumb_x, thumb_y = big_toe_point
    little_x, little_y = little_toe_point

    # 1. Draw Line from Heel to Big Toe
    cv2.line(imagen, (int(heel_x), int(heel_y)), (int(thumb_x), int(thumb_y)), white_color, line_thickness)

    # Draw red crosses at the ends of the line
    imagen = dibujar_cruz(imagen, (int(heel_x), int(heel_y)), red_color, size=20, thickness=2)
    imagen = dibujar_cruz(imagen, (int(thumb_x), int(thumb_y)), red_color, size=20, thickness=2)

    # 2. Draw Horizontal Line Near the Bottom of the Heel (unchanged)
    heel_y = int(heel_y)
    foot_height = heel_y - contour_points[:, 1].min()
    horizontal_line_y = heel_y - int(0.1 * foot_height)

    # Find intersection points at this y-coordinate
    tolerance = 5  # pixels
    horizontal_points = contour_points[np.abs(contour_points[:, 1] - horizontal_line_y) <= tolerance]
    if horizontal_points.size >= 2:
        horizontal_points = horizontal_points[horizontal_points[:, 0].argsort()]
        start_point = horizontal_points[0]
        end_point = horizontal_points[-1]
    else:
        x_min = contour_points[:, 0].min()
        x_max = contour_points[:, 0].max()
        start_point = (x_min, horizontal_line_y)
        end_point = (x_max, horizontal_line_y)

    # Draw horizontal line
    cv2.line(imagen, (int(start_point[0]), int(start_point[1])), (int(end_point[0]), int(end_point[1])), white_color, line_thickness)

    # Draw red crosses at the ends of the horizontal line
    imagen = dibujar_cruz(imagen, (int(start_point[0]), int(start_point[1])), red_color, size=20, thickness=2)
    imagen = dibujar_cruz(imagen, (int(end_point[0]), int(end_point[1])), red_color, size=20, thickness=2)

    # 3. Draw Line Across the Metatarsals (Below the Toes)
    # Find the widest part of the foot (maximum width) below the toes
    # We'll scan through the foot contour from top to bottom to find where the width is maximum

    y_values = np.arange(int(thumb_y), heel_y, 5)  # Scan from toes to heel
    max_width = 0
    metatarsal_line_y = thumb_y  # Initialize at toe level

    for y in y_values:
        # Find all contour points at this y-coordinate
        points_at_y = contour_points[np.abs(contour_points[:, 1] - y) <= tolerance]
        if points_at_y.size >= 2:
            x_coords = points_at_y[:, 0]
            width_at_y = x_coords.max() - x_coords.min()
            if width_at_y > max_width:
                max_width = width_at_y
                metatarsal_line_y = y

    # Now, get the points at metatarsal_line_y
    metatarsal_points = contour_points[np.abs(contour_points[:, 1] - metatarsal_line_y) <= tolerance]
    if metatarsal_points.size >= 2:
        metatarsal_points = metatarsal_points[metatarsal_points[:, 0].argsort()]
        start_point = metatarsal_points[0]
        end_point = metatarsal_points[-1]
    else:
        # Default to using the widest x-coordinates if no points found
        x_min = contour_points[:, 0].min()
        x_max = contour_points[:, 0].max()
        start_point = (x_min, metatarsal_line_y)
        end_point = (x_max, metatarsal_line_y)

    # Draw line across metatarsals
    cv2.line(imagen, (int(start_point[0]), int(metatarsal_line_y)), (int(end_point[0]), int(metatarsal_line_y)), white_color, line_thickness)

    # Draw red crosses at the ends of the metatarsal line
    imagen = dibujar_cruz(imagen, (int(start_point[0]), int(metatarsal_line_y)), red_color, size=20, thickness=2)
    imagen = dibujar_cruz(imagen, (int(end_point[0]), int(metatarsal_line_y)), red_color, size=20, thickness=2)

    return imagen

def dibujar_cruz(imagen, punto, color, size=20, thickness=2):
    """
    Draws a cross marker at the specified point.

    Args:
        imagen (np.ndarray): Image on which to draw.
        punto (tuple): (x, y) coordinates of the center of the cross.
        color (tuple): BGR color for the cross.
        size (int): Size of the cross.
        thickness (int): Thickness of the cross lines.

    Returns:
        np.ndarray: Image with the cross drawn.
    """
    x, y = punto
    # Ensure the point is within the image boundaries
    x = int(max(0, min(x, imagen.shape[1] - 1)))
    y = int(max(0, min(y, imagen.shape[0] - 1)))
    # Horizontal line of the cross
    cv2.line(imagen, (x - size // 2, y), (x + size // 2, y), color, thickness)
    # Vertical line of the cross
    cv2.line(imagen, (x, y - size // 2), (x, y + size // 2), color, thickness)
    return imagen

def agregar_logotipo(imagen, ruta_logotipo):
    """
    Adds a logo to the bottom right corner of the image, maintaining aspect ratio.

    Args:
        imagen (np.ndarray): Image to which the logo will be added.
        ruta_logotipo (str): Path to the logo file.

    Returns:
        np.ndarray: Image with the logo added.
    """
    logotipo = cv2.imread(ruta_logotipo, cv2.IMREAD_UNCHANGED)
    if logotipo is None:
        print(f"No se pudo cargar el logotipo: {ruta_logotipo}")
        return imagen

    # Calculate the maximum allowed size for the logo (50% of the image width)
    alto, ancho = imagen.shape[:2]
    max_logo_width = int(ancho * 0.5)  # Increased size to 50%
    max_logo_height = int(alto * 0.5)
    
    # Maintain aspect ratio when resizing the logo
    logo_height, logo_width = logotipo.shape[:2]
    scale = min(max_logo_width / logo_width, max_logo_height / logo_height)
    logo_new_width = int(logo_width * scale)
    logo_new_height = int(logo_height * scale)
    logotipo = cv2.resize(logotipo, (logo_new_width, logo_new_height), interpolation=cv2.INTER_AREA)

    # Position the logo in the bottom right corner with 10 px padding (less padding)
    x_offset = ancho - logo_new_width - 10
    y_offset = alto - logo_new_height - 10

    if logotipo.shape[2] == 4:
        # Handle transparent logos (alpha channel)
        alpha = logotipo[:, :, 3] / 255.0
        logo_rgb = logotipo[:, :, :3]
        roi = imagen[y_offset:y_offset+logo_new_height, x_offset:x_offset+logo_new_width]

        for c in range(0, 3):
            roi[:, :, c] = (alpha * logo_rgb[:, :, c] + (1 - alpha) * roi[:, :, c])
        imagen[y_offset:y_offset+logo_new_height, x_offset:x_offset+logo_new_width] = roi
    else:
        # Overlay the logo without transparency
        imagen[y_offset:y_offset+logo_new_height, x_offset:x_offset+logo_new_width] = logotipo

    return imagen
