import win32com.client
import pythoncom
import tempfile
import cv2
import os
import uuid

def scan_image():
    pythoncom.CoInitialize()
    try:
        # Initialize WIA DeviceManager
        device_manager = win32com.client.Dispatch("WIA.DeviceManager")
        
        # Get the first available scanner device
        scanner = None
        for device_info in device_manager.DeviceInfos:
            if device_info.Type == 1:  # 1 indicates scanner device
                scanner = device_info.Connect()
                break
        
        if scanner is None:
            raise Exception("No se encontraron dispositivos de escaneo.")
        
        # Get the scanner item
        scan_item = scanner.Items[1]  # Usually the first item

        # Set properties
        props = scan_item.Properties

        # Set DataType to Color (PropertyID 4103)
        if props.Exists(4103):
            props[4103].Value = 1  # WIA_DATA_COLOR
        else:
            print("El dispositivo no admite el ajuste del tipo de datos a color.")

        # Set Resolution to 300 DPI (PropertyIDs 6147 and 6148)
        if props.Exists(6147):  # Horizontal Resolution
            props[6147].Value = 300
        if props.Exists(6148):  # Vertical Resolution
            props[6148].Value = 300

        # Set Brightness (PropertyID 6154)
        if props.Exists(6154):
            brightness_prop = props[6154]
            brightness_min = brightness_prop.SubTypeMin
            brightness_max = brightness_prop.SubTypeMax
            # Ensure the value is within range
            brightness_value = 1000
            brightness_value = min(max(brightness_value, brightness_min), brightness_max)
            brightness_prop.Value = brightness_value
        else:
            print("El dispositivo no admite el ajuste de brillo.")

        # Set Contrast (PropertyID 6155)
        if props.Exists(6155):
            contrast_prop = props[6155]
            contrast_min = contrast_prop.SubTypeMin
            contrast_max = contrast_prop.SubTypeMax
            # Ensure the value is within range
            contrast_value = 800
            contrast_value = min(max(contrast_value, contrast_min), contrast_max)
            contrast_prop.Value = contrast_value
        else:
            print("El dispositivo no admite el ajuste de contraste.")

        # Acquire image
        image = scan_item.Transfer()

        # Create a unique temporary filename
        temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")
        
        # Save the image
        image.SaveFile(temp_filename)
        
        # Read the image using OpenCV
        scanned_image = cv2.imread(temp_filename)
        if scanned_image is None:
            raise Exception("La imagen escaneada está vacía o no se pudo leer correctamente.")

        # Delete the temp file
        os.unlink(temp_filename)

        return scanned_image

    except Exception as e:
        raise Exception(f"Error al escanear la imagen: {str(e)}")
    finally:
        pythoncom.CoUninitialize()
