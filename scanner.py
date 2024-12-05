def scan_image():
    print("Escaneada")

    return None

# # scanner.py
# import win32com.client
# import pythoncom
# import tempfile
# import cv2
# import os
# import uuid

# def scan_image():
#     pythoncom.CoInitialize()
#     try:
#         # Inicializar el diálogo común de WIA
#         common_dialog = win32com.client.Dispatch("WIA.CommonDialog")
        
#         # Mostrar el diálogo de adquisición de imagen
#         image = common_dialog.ShowAcquireImage(
#             FormatID="{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}",  # Formato BMP
#             Intent=1,  # wiaIntentImageTypeColor para Color
#             DeviceType=1,  # Tipo de dispositivo: Escáner
#             CancelError=True  # Lanzar una excepción si el usuario cancela
#         )

#         # Crear un nombre de archivo temporal único
#         temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")
        
#         # Guardar la imagen escaneada en el archivo temporal
#         image.SaveFile(temp_filename)

#         # Leer la imagen usando OpenCV
#         scanned_image = cv2.imread(temp_filename)
#         if scanned_image is None:
#             raise Exception("La imagen escaneada está vacía o no se pudo leer correctamente.")

#         # Eliminar el archivo temporal
#         os.unlink(temp_filename)

#         return scanned_image

#     except Exception as e:
#         raise Exception(f"Error al escanear la imagen: {str(e)}")
#     finally:
#         pythoncom.CoUninitialize()