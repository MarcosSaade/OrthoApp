# image_processing.py

import cv2
import numpy as np
import os

def procesar_imagen(ruta, ruta_logotipo, recolor=True, image=None, foot_side="right"):
    if image is not None:
        imagen = image.copy()
    elif ruta:
        imagen = cv2.imread(ruta)
    else:
        raise ValueError("Debe proporcionar una ruta de imagen o una imagen.")

    if imagen is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {ruta}")

    # Flip horizontally to maintain orientation
    imagen = cv2.flip(imagen, 1)

    height, width = imagen.shape[:2]
    mask_ellipse = np.zeros((height, width), dtype=np.uint8)
    center = (width // 2, height // 2)
    axes = (width // 3, height)
    cv2.ellipse(mask_ellipse, center, axes, 0, 0, 360, 255, -1)
    imagen = cv2.bitwise_and(imagen, imagen, mask=mask_ellipse)

    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)

    lower_skin = np.array([0, 100, 100], dtype=np.uint8)
    upper_skin = np.array([140, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    mask = cv2.GaussianBlur(mask, (7, 7), 0)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=35)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    refined_mask = np.zeros_like(mask)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(refined_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    else:
        raise ValueError("No se encontró ninguna forma de pie en la imagen.")

    imagen_sin_fondo = cv2.bitwise_and(imagen, imagen, mask=refined_mask)

    if recolor:
        fondo_blanco = np.ones_like(imagen) * 255
        mask_inv = cv2.bitwise_not(refined_mask)
        fondo = cv2.bitwise_and(fondo_blanco, fondo_blanco, mask=mask_inv)
        imagen_con_fondo_blanco = cv2.add(fondo, imagen_sin_fondo)

        imagen_gris = cv2.cvtColor(imagen_con_fondo_blanco, cv2.COLOR_BGR2GRAY)
        imagen_normalizada = cv2.normalize(imagen_gris, None, 0, 255, cv2.NORM_MINMAX)

        heatmap = cv2.applyColorMap(imagen_normalizada, cv2.COLORMAP_JET)
        refined_mask_3ch = cv2.cvtColor(refined_mask, cv2.COLOR_GRAY2BGR)
        heatmap_foreground = cv2.bitwise_and(heatmap, refined_mask_3ch)
        final_image = cv2.add(fondo, heatmap_foreground)
    else:
        fondo_blanco = np.ones_like(imagen) * 255
        mask_inv = cv2.bitwise_not(refined_mask)
        fondo = cv2.bitwise_and(fondo_blanco, fondo_blanco, mask=mask_inv)
        final_image = cv2.add(fondo, imagen_sin_fondo)

    final_image = agregar_lineas(final_image, largest_contour, foot_side)

    if ruta_logotipo and os.path.exists(ruta_logotipo):
        final_image = agregar_logotipo(final_image, ruta_logotipo)

    return final_image

def agregar_lineas(imagen, foot_contour, foot_side="right"):
    height, width = imagen.shape[:2]
    line_thickness = 5
    white_color = (255, 255, 255)
    red_color = (0, 0, 255)

    contour_points = foot_contour.reshape(-1, 2)
    heel_point = contour_points[contour_points[:, 1].argmax()]
    heel_x, heel_y = heel_point

    top_points = contour_points[contour_points[:, 1] <= contour_points[:, 1].min() + 0.05 * height]

    if foot_side.lower() == "right":
        big_toe_point = top_points[top_points[:, 0].argmin()]
        little_toe_point = top_points[top_points[:, 0].argmax()]
    else:
        big_toe_point = top_points[top_points[:, 0].argmax()]
        little_toe_point = top_points[top_points[:, 0].argmin()]

    thumb_x, thumb_y = big_toe_point
    little_x, little_y = little_toe_point

    cv2.line(imagen, (int(heel_x), int(heel_y)), (int(thumb_x), int(thumb_y)), white_color, line_thickness)
    imagen = dibujar_cruz(imagen, (int(heel_x), int(heel_y)), red_color, size=20, thickness=2)
    imagen = dibujar_cruz(imagen, (int(thumb_x), int(thumb_y)), red_color, size=20, thickness=2)

    heel_y = int(heel_y)
    foot_height = heel_y - contour_points[:, 1].min()
    horizontal_line_y = heel_y - int(0.1 * foot_height)

    tolerance = 5
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

    cv2.line(imagen, (int(start_point[0]), int(start_point[1])), (int(end_point[0]), int(end_point[1])), white_color, line_thickness)
    imagen = dibujar_cruz(imagen, (int(start_point[0]), int(start_point[1])), red_color, size=20, thickness=2)
    imagen = dibujar_cruz(imagen, (int(end_point[0]), int(end_point[1])), red_color, size=20, thickness=2)

    y_values = np.arange(int(thumb_y), heel_y, 5)
    max_width = 0
    metatarsal_line_y = thumb_y

    for y in y_values:
        points_at_y = contour_points[np.abs(contour_points[:, 1] - y) <= tolerance]
        if points_at_y.size >= 2:
            x_coords = points_at_y[:, 0]
            width_at_y = x_coords.max() - x_coords.min()
            if width_at_y > max_width:
                max_width = width_at_y
                metatarsal_line_y = y

    metatarsal_points = contour_points[np.abs(contour_points[:, 1] - metatarsal_line_y) <= tolerance]
    if metatarsal_points.size >= 2:
        metatarsal_points = metatarsal_points[metatarsal_points[:, 0].argsort()]
        start_point = metatarsal_points[0]
        end_point = metatarsal_points[-1]
    else:
        x_min = contour_points[:, 0].min()
        x_max = contour_points[:, 0].max()
        start_point = (x_min, metatarsal_line_y)
        end_point = (x_max, metatarsal_line_y)

    cv2.line(imagen, (int(start_point[0]), int(metatarsal_line_y)), (int(end_point[0]), int(metatarsal_line_y)), white_color, line_thickness)
    imagen = dibujar_cruz(imagen, (int(start_point[0]), int(metatarsal_line_y)), red_color, size=20, thickness=2)
    imagen = dibujar_cruz(imagen, (int(end_point[0]), int(metatarsal_line_y)), red_color, size=20, thickness=2)

    return imagen

def dibujar_cruz(imagen, punto, color, size=20, thickness=2):
    x, y = punto
    x = int(max(0, min(x, imagen.shape[1] - 1)))
    y = int(max(0, min(y, imagen.shape[0] - 1)))
    cv2.line(imagen, (x - size // 2, y), (x + size // 2, y), color, thickness)
    cv2.line(imagen, (x, y - size // 2), (x, y + size // 2), color, thickness)
    return imagen

def agregar_logotipo(imagen, ruta_logotipo):
    logotipo = cv2.imread(ruta_logotipo, cv2.IMREAD_UNCHANGED)
    if logotipo is None:
        return imagen

    alto, ancho = imagen.shape[:2]
    max_logo_width = int(ancho * 0.5)
    max_logo_height = int(alto * 0.5)
    
    logo_height, logo_width = logotipo.shape[:2]
    scale = min(max_logo_width / logo_width, max_logo_height / logo_height)
    logo_new_width = int(logo_width * scale)
    logo_new_height = int(logo_height * scale)
    logotipo = cv2.resize(logotipo, (logo_new_width, logo_new_height), interpolation=cv2.INTER_AREA)

    x_offset = ancho - logo_new_width - 10
    y_offset = alto - logo_new_height - 10

    if logotipo.shape[2] == 4:
        alpha = logotipo[:, :, 3] / 255.0
        logo_rgb = logotipo[:, :, :3]
        roi = imagen[y_offset:y_offset+logo_new_height, x_offset:x_offset+logo_new_width]

        for c in range(0, 3):
            roi[:, :, c] = (alpha * logo_rgb[:, :, c] + (1 - alpha) * roi[:, :, c])
        imagen[y_offset:y_offset+logo_new_height, x_offset:x_offset+logo_new_width] = roi
    else:
        imagen[y_offset:y_offset+logo_new_height, x_offset:x_offset+logo_new_width] = logotipo

    return imagen
