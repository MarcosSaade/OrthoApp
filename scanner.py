# scanner.py
import win32com.client
import pythoncom
import tempfile
import cv2
import os
import uuid

def SetWIAProperty(properties, prop_name, prop_value):
    """
    Establece el valor de una propiedad WIA específica.
    
    :param properties: Colección de propiedades del dispositivo WIA.
    :param prop_name: Nombre de la propiedad a establecer.
    :param prop_value: Valor que se asignará a la propiedad.
    """
    for prop in properties:
        if prop.Name == prop_name:
            prop.Value = prop_value
            return
    raise Exception(f"No se encontró la propiedad '{prop_name}'")

def scan_image():
    """
    Escanea una imagen utilizando el escáner WIA sin mostrar el diálogo del sistema.
    Ajusta las propiedades del escaneo según las especificaciones personalizadas:
    - Resolución: 100 DPI
    - Brillo: Máximo (100)
    - Contraste: 80
    - Intención: Color

    Después del escaneo, muestra la imagen escaneada en una ventana para depuración.

    :return: Imagen escaneada como un objeto de OpenCV (numpy.ndarray).
    """
    pythoncom.CoInitialize()
    try:
        # Crear un DeviceManager para obtener el dispositivo de escáner
        device_manager = win32com.client.Dispatch("WIA.DeviceManager")
        
        if device_manager.DeviceInfos.Count == 0:
            raise Exception("No se encontró ningún dispositivo WIA conectado.")

        # Suponiendo que el primer dispositivo encontrado es el escáner que queremos usar
        # (Si hubiera más de uno, se debería implementar una lógica para seleccionar el adecuado)
        device = device_manager.DeviceInfos.Item(1).Connect()
        
        # Obtener el objeto del ítem del escáner (normalmente el primero)
        scanner_item = device.Items.Item(1)

        # Ajustar las propiedades del escaneo:
        # - Resolución: 100 DPI
        # - Brillo: máximo (100)
        # - Contraste: 80
        # - Intención: color (1)
        try:
            SetWIAProperty(scanner_item.Properties, "Horizontal Resolution", 100)
            SetWIAProperty(scanner_item.Properties, "Vertical Resolution", 100)
            SetWIAProperty(scanner_item.Properties, "Brightness", 100)
            SetWIAProperty(scanner_item.Properties, "Contrast", 80)
            SetWIAProperty(scanner_item.Properties, "Intent", 1)  # 1 = Color
        except Exception as prop_error:
            raise Exception(f"Error al configurar las propiedades del escaneo: {prop_error}")

        # Adquirir la imagen directamente sin mostrar el diálogo
        # Formato BMP: {B96B3CAB-0728-11D3-9D7B-0000F81EF32E}
        try:
            image = scanner_item.Transfer("{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}")
        except Exception as transfer_error:
            raise Exception(f"Error al transferir la imagen desde el escáner: {transfer_error}")

        # Crear un nombre de archivo temporal único
        temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")

        # Guardar la imagen en el archivo temporal
        try:
            image.SaveFile(temp_filename)
        except Exception as save_error:
            raise Exception(f"Error al guardar la imagen escaneada: {save_error}")

        # Leer la imagen usando OpenCV
        scanned_image = cv2.imread(temp_filename)
        if scanned_image is None:
            raise Exception("La imagen escaneada está vacía o no se pudo leer correctamente.")

        # Mostrar la imagen en una ventana para depuración
        cv2.imshow('Imagen Escaneada para Depuración', scanned_image)
        print("Presione cualquier tecla en la ventana de la imagen para continuar...")
        cv2.waitKey(0)  # Espera a que el usuario presione una tecla
        cv2.destroyAllWindows()

        # Eliminar el archivo temporal
        os.remove(temp_filename)

        return scanned_image

    except Exception as e:
        # Manejo de errores: imprimir el error y re-raise
        print(f"Error al escanear la imagen: {e}")
        raise
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    try:
        image = scan_image()
        # Aquí puedes agregar cualquier procesamiento adicional de la imagen si es necesario
        print("Escaneo completado exitosamente.")
    except Exception as scan_exception:
        print(f"El escaneo falló: {scan_exception}")
