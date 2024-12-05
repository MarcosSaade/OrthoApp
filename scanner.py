# scanner.py
import win32com.client
import pythoncom
import tempfile
import cv2
import os
import uuid

def scan_image():
    pythoncom.CoInitialize()
    try:
        # Inicializar el administrador de dispositivos WIA
        device_manager = win32com.client.Dispatch("WIA.DeviceManager")
        devices = device_manager.DeviceInfos

        if len(devices) == 0:
            raise Exception("No se encontraron dispositivos WIA conectados.")

        # Seleccionar el primer escáner disponible
        scanner = None
        for device_info in devices:
            if device_info.Type == 1:  # 1 corresponde a dispositivos de escáner
                scanner = device_info.Connect()
                break

        if scanner is None:
            raise Exception("No se encontró ningún escáner conectado.")

        # Seleccionar el primer ítem del escáner (generalmente el escáner plano)
        scan_item = scanner.Items[1]  # Los ítems están indexados a partir de 1

        # Configurar las propiedades de digitalización
        properties = scan_item.Properties

        # Definir los IDs de las propiedades de brillo y contraste
        WIA_IPS_BRIGHTNESS = "6146"
        WIA_IPS_CONTRAST = "6147"

        # Establecer el brillo
        if WIA_IPS_BRIGHTNESS in [prop.PropertyID for prop in properties]:
            brightness = scan_item.Properties(WIA_IPS_BRIGHTNESS)
            brightness.Value = 1000  # Ajusta este valor según el rango soportado por tu escáner
        else:
            print("La propiedad de brillo no está disponible en este escáner.")

        # Establecer el contraste
        if WIA_IPS_CONTRAST in [prop.PropertyID for prop in properties]:
            contrast = scan_item.Properties(WIA_IPS_CONTRAST)
            contrast.Value = 800  # Ajusta este valor según el rango soportado por tu escáner
        else:
            print("La propiedad de contraste no está disponible en este escáner.")

        # Realizar la digitalización en formato BMP
        image = scan_item.Transfer("{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}")  # Formato BMP

        # Crear un nombre de archivo temporal único
        temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")

        # Guardar la imagen escaneada en el archivo temporal
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

if __name__ == "__main__":
    try:
        image = scan_image()
        # Aquí puedes procesar la imagen escaneada según tus necesidades
        # Por ejemplo, mostrarla usando OpenCV
        cv2.imshow("Imagen Escaneada", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as error:
        print(error)
