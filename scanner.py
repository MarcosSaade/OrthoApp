# scanner.py
import win32com.client
import pythoncom
import tempfile
import cv2
import os
import uuid

# Flag to control whether to show the scanned image for testing
TEST_SCAN = True

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

        # Access scanner properties
        props = scan_item.Properties

        # Function to set a property with desired value
        def set_property(prop_id, desired_value, description):
            if props.Exists(prop_id):
                prop = props[prop_id]
                min_val = prop.SubTypeMin
                max_val = prop.SubTypeMax
                # Clamp the desired value within the allowed range
                value = min(max(desired_value, min_val), max_val)
                prop.Value = value
                print(f"{description} establecido a: {value} (Rango: {min_val} - {max_val})")
            else:
                print(f"El dispositivo no admite el ajuste de {description.lower()} (Property ID: {prop_id}).")

        # Set DataType to Color (PropertyID 4103)
        DATA_TYPE_COLOR = 1  # WIA_DATA_COLOR
        DATA_TYPE_GRAYSCALE = 0  # WIA_DATA_GRAYSCALE
        DATA_TYPE_TEXT = 2  # WIA_DATA_TEXT
        DATA_TYPE_RAW = 4  # WIA_DATA_RAW

        DATA_TYPE_PROPERTY_ID = 4103  # WIA_IPA_DATATYPE
        if props.Exists(DATA_TYPE_PROPERTY_ID):
            props[DATA_TYPE_PROPERTY_ID].Value = DATA_TYPE_COLOR
            print("Tipo de datos establecido a Color.")
        else:
            print("El dispositivo no admite el ajuste del tipo de datos a color.")

        # Set Resolution to 300 DPI (PropertyIDs 6147 and 6148)
        HORIZONTAL_RESOLUTION_ID = 6147  # WIA_IPS_XRES
        VERTICAL_RESOLUTION_ID = 6148    # WIA_IPS_YRES
        set_property(HORIZONTAL_RESOLUTION_ID, 300, "Resolución horizontal (DPI)")
        set_property(VERTICAL_RESOLUTION_ID, 300, "Resolución vertical (DPI)")

        # Set Brightness to maximum
        BRIGHTNESS_PROPERTY_ID = 6154  # WIA_IPS_BRIGHTNESS
        if props.Exists(BRIGHTNESS_PROPERTY_ID):
            brightness_prop = props[BRIGHTNESS_PROPERTY_ID]
            brightness_max = brightness_prop.SubTypeMax
            set_property(BRIGHTNESS_PROPERTY_ID, brightness_max, "Brillo")
        else:
            print("El dispositivo no admite el ajuste de brillo.")

        # Set Contrast to 80% of maximum
        CONTRAST_PROPERTY_ID = 6155  # WIA_IPS_CONTRAST
        if props.Exists(CONTRAST_PROPERTY_ID):
            contrast_prop = props[CONTRAST_PROPERTY_ID]
            contrast_max = contrast_prop.SubTypeMax
            contrast_value = int(contrast_max * 0.8)
            set_property(CONTRAST_PROPERTY_ID, contrast_value, "Contraste")
        else:
            print("El dispositivo no admite el ajuste de contraste.")

        # Acquire image
        print("Iniciando la adquisición de la imagen...")
        image = scan_item.Transfer()

        # Create a unique temporary filename
        temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")
        
        # Save the image
        image.SaveFile(temp_filename)
        print(f"Imagen guardada temporalmente en: {temp_filename}")
        
        # Read the image using OpenCV
        scanned_image = cv2.imread(temp_filename)
        if scanned_image is None:
            raise Exception("La imagen escaneada está vacía o no se pudo leer correctamente.")

        # Delete the temp file
        os.unlink(temp_filename)
        print("Archivo temporal eliminado.")

        # If TEST_SCAN is True, display the scanned image for debugging
        if TEST_SCAN:
            cv2.imshow("Scanned Image - Original", scanned_image)
            print("Presione cualquier tecla en la ventana de la imagen para continuar...")
            cv2.waitKey(0)  # Wait indefinitely until a key is pressed
            cv2.destroyAllWindows()

        return scanned_image

    except Exception as e:
        raise Exception(f"Error al escanear la imagen: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    # Example usage
    try:
        image = scan_image()
        # Aquí puedes agregar más procesamiento de la imagen si lo deseas
    except Exception as error:
        print(error)
