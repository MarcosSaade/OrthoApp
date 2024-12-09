# Orto-Flex Scanner

![image](https://github.com/user-attachments/assets/c4afe8e9-e208-4de7-a672-6ef9e1e01a9c)
*Main application window showcasing image display and action buttons.*


## Overview

Orto-Flex Scanner is a sophisticated desktop application designed specifically for orthopedics clinics. It seamlessly integrates with scanners to capture high-quality images of patients' feet, processes these images by removing backgrounds and generating heatmaps, and compiles comprehensive PDF reports. The application boasts a user-friendly interface built with PyQt5, ensuring ease of use for medical professionals.

## Features

- **Intuitive User Interface:** Clean and responsive UI built with PyQt5 for effortless navigation and operation.
- **Seamless Scanner Integration:** Directly interfaces with scanners to capture images in both test and production modes.
- **Advanced Image Processing:** Utilizes OpenCV to remove backgrounds and generate detailed heatmap images.
- **Comprehensive PDF Reports:** Generates professional PDF reports incorporating processed images and patient information using ReportLab.
- **Customizable Patient Information:** Collects and manages detailed patient data, including contact information and specific medical details.
- **Robust Error Handling:** Provides informative messages and handles exceptions gracefully to ensure a smooth user experience.
- **Persistent Settings:** Remembers user preferences and last accessed directories using QSettings.
- **Multi-Language Support:** Currently supports Spanish, with the potential for multilingual extensions.

## Technologies Used

- **Python 3.8+**
- **PyQt5:** For building the graphical user interface.
- **OpenCV:** For image processing tasks including background removal and heatmap generation.
- **ReportLab:** For creating PDF reports.
- **NumPy:** For efficient numerical operations on image data.
- **Other Libraries:** Utilizes various Python libraries for file handling, GUI components, and more.
