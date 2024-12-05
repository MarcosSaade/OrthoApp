# scanner.py
import win32com.client
import pythoncom
import tempfile
import cv2
import os
import uuid

def scan_image(brightness=0, contrast=0):
    pythoncom.CoInitialize()
    try:
        # Initialize WIA Device Manager
        device_manager = win32com.client.Dispatch("WIA.DeviceManager")
        
        # Select the first available scanner
        scanner = None
        for device in device_manager.DeviceInfos:
            if device.Type == 1:  # 1 corresponds to scanners
                scanner = device.Connect()
                break
        
        if scanner is None:
            raise Exception("No scanner found. Please ensure a scanner is connected.")
        
        # Access the scanner's item (the scanning device)
        scan_item = scanner.Items[1]
        
        # Define scan properties
        properties = scan_item.Properties
        
        # Set DPI (resolution)
        properties["6147"].Value = 300  # Horizontal Resolution
        properties["6148"].Value = 300  # Vertical Resolution
        
        # Set color mode
        # 1 = Grayscale, 2 = Color, 4 = Black & White
        properties["6151"].Value = 2  # Color
        
        # Set brightness and contrast
        # Property IDs for brightness and contrast
        properties["6154"].Value = brightness  # Brightness adjustment
        properties["6155"].Value = contrast   # Contrast adjustment
        
        # Set format to BMP
        format_id = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
        
        # Perform the scan
        image = scan_item.Transfer(format_id)
        
        # Create a unique temporary filename
        temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")
        
        # Save the image to the temporary file
        image.SaveFile(temp_filename)
        
        # Load the image using OpenCV
        scanned_image = cv2.imread(temp_filename)
        if scanned_image is None:
            raise Exception("Scanned image is empty or could not be read properly.")
        
        # Delete the temporary file
        os.unlink(temp_filename)
        
        return scanned_image
    
    except Exception as e:
        raise Exception(f"Error scanning image: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

# Example usage
if __name__ == "__main__":
    try:
        # Example: Scan with brightness +50 and contrast +30
        img = scan_image(brightness=50, contrast=30)
        cv2.imshow("Scanned Image", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as error:
        print(error)
