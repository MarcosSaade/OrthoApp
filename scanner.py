# scanner.py
import win32com.client
import pythoncom
import tempfile
import cv2
import os
import uuid

def SetWIAProperty(properties, prop_name, prop_value):
    for prop in properties:
        if prop.Name == prop_name:
            prop.Value = prop_value
            return
    raise Exception(f"No se encontró la propiedad {prop_name}")

def scan_image():
    pythoncom.CoInitialize()
    try:
        # Crear un DeviceManager para obtener el dispositivo de escáner
        device_manager = win32com.client.Dispatch("WIA.DeviceManager")
        
        # Suponiendo que el primer dispositivo encontrado es el escáner que queremos usar
        # (Si hubiera más de uno, se debería elegir el adecuado)
        device = device_manager.DeviceInfos[0].Connect()
        
        # Obtener el objeto del ítem del escáner (normalmente el primero)
        scanner_item = device.Items[0]

        # Ajustar las propiedades del escaneo:
        # Según el requerimiento: 
        # - Ajustar a "custom" (que el cliente definió como máximo brillo, 80% contraste, 100DPI)
        # - Sin que aparezca el diálogo.
        
        # Establecer resolución horizontal y vertical a 100 DPI
        SetWIAProperty(scanner_item.Properties, "Horizontal Resolution", 100)
        SetWIAProperty(scanner_item.Properties, "Vertical Resolution", 100)

        # Ajustar el brillo y el contraste. 
        # Suponiendo que "máximo brillo" es el valor máximo permitido (normalmente 100)
        # y "80% de contraste máximo" asumiendo el máximo también es 100, pues 80.
        SetWIAProperty(scanner_item.Properties, "Brightness", 100)
        SetWIAProperty(scanner_item.Properties, "Contrast", 80)

        # Ajustar la intención actual a color (1 = color)
        SetWIAProperty(scanner_item.Properties, "Current Intent", 1)
        
        # Adquirir la imagen directamente sin mostrar el diálogo
        # Formato BMP: {B96B3CAB-0728-11D3-9D7B-0000F81EF32E}
        image = scanner_item.Transfer("{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}")

        # Crear un nombre de archivo temporal único
        temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")

        # Guardar la imagen en el archivo temporal
        image.SaveFile(temp_filename)

        # Leer la imagen usando OpenCV
        scanned_image = cv2.imread(temp_filename)
        if scanned_image is None:
            raise Exception("La imagen escaneada está vacía o no se pudo leer correctamente.")

        # Eliminar el archivo temporal
        os.unlink(temp_filename)

        return scanned_image

    except Exception as e:
        raise Exception(f"Error al escanear la imagen: {str(e)}")
    finally:
        pythoncom.CoUninitialize()
