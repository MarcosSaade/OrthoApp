# scanner.py
import win32com.client
import pythoncom
import tempfile
import cv2
import os
import uuid
import threading
import time
from pywinauto import Application, timings
from pywinauto.keyboard import send_keys

def automate_dialog():
    """
    Automate the WIA dialog to select the fourth option (Personalized Configuration)
    and press Enter.
    """
    try:
        # Wait briefly to ensure the dialog has appeared
        time.sleep(1)  # Adjust if necessary

        # Connect to the WIA dialog window
        app = Application(backend="uia").connect(title_re=".*Windows Image Acquisition.*")
        dlg = app.window(title_re=".*Windows Image Acquisition.*")

        # Set focus to the dialog
        dlg.set_focus()

        # Depending on the dialog structure, identify and interact with the correct control.
        # This example assumes that the options are RadioButtons within a GroupBox.

        # Example: Selecting the fourth RadioButton
        # Adjust the control identifiers based on actual inspection
        # You might need to navigate through panes or group boxes

        # Expand the dialog's control hierarchy
        dlg.print_control_identifiers()

        # Example Approach:
        # Assume options are in a List or as RadioButtons named "Option 4"
        # Modify the control path based on actual UI structure

        # Option 1: Using RadioButton with a specific title or automation ID
        try:
            # Attempt to select the RadioButton directly by index
            radio_buttons = dlg.descendants(control_type="RadioButton")
            if len(radio_buttons) >= 4:
                radio_buttons[3].select()  # Zero-based index
                print("Selected the fourth option (Personalized Configuration).")
            else:
                print(f"Expected at least 4 radio buttons, found {len(radio_buttons)}.")
        except Exception as e:
            print(f"Error selecting RadioButton: {e}")

        # Option 2: Using keyboard navigation
        # If RadioButtons cannot be easily identified, navigate using keyboard
        # For example, pressing 'Tab' to focus and arrow keys to select
        # This method is less reliable but can be a fallback

        # Uncomment the following lines if Option 1 doesn't work
        """
        send_keys("{TAB}")  # Navigate to the options
        send_keys("{DOWN 3}")  # Move down to the fourth option
        """

        # Press Enter to confirm selection
        send_keys("{ENTER}")
        print("Pressed Enter to confirm selection.")

    except Exception as e:
        print(f"Failed to automate dialog: {e}")

def scan_image():
    pythoncom.CoInitialize()
    try:
        # Initialize the WIA CommonDialog
        common_dialog = win32com.client.Dispatch("WIA.CommonDialog")
        
        # Start the automation in a separate thread
        automation_thread = threading.Thread(target=automate_dialog, daemon=True)
        automation_thread.start()
        
        # Show the scanner dialog
        image = common_dialog.ShowAcquireImage(
            FormatID="{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}",  # BMP FormatID
            Intent=4,  # Adjust Intent if necessary (e.g., wiaIntentImageTypeText)
            DeviceType=1,  # Device type: Scanner
            CancelError=True  # Raise an exception if the user cancels
        )

        # Generate a unique temporary filename
        temp_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.bmp")

        # Save the scanned image to the temporary file
        image.SaveFile(temp_filename)

        # Read the image using OpenCV
        scanned_image = cv2.imread(temp_filename)
        if scanned_image is None:
            raise Exception("La imagen escaneada está vacía o no se pudo leer correctamente.")

        # Delete the temporary file
        os.unlink(temp_filename)

        return scanned_image

    except Exception as e:
        raise Exception(f"Error al escanear la imagen: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

# Example usage
if __name__ == "__main__":
    try:
        image = scan_image()
        # Display the image using OpenCV (optional)
        cv2.imshow("Scanned Image", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as error:
        print(error)
