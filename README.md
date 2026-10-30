# Orto-Flex Scanner

A desktop app for orthopedic clinics that turns a flatbed scan of a patient's feet into measurements, a pressure-style heatmap and a branded PDF report for ordering custom insoles. I built it as a freelance project for Orto-Flex in 2024. It is in daily use at two clinics that see about 4,000 patients a year, and it cut the time per scan by about 70% (from roughly 10 minutes of manual work to under 3).

![Main window](https://github.com/user-attachments/assets/c4afe8e9-e208-4de7-a672-6ef9e1e01a9c)
*Main window: left and right foot scans with the processed result.*

## The problem

The clinics scanned feet with a generic scanner, drew measurements by hand and assembled reports manually, so every patient took about 10 minutes and reports were inconsistent between staff and clinics.

## What it does

1. **Capture.** Scan each foot directly from the app (Windows, through WIA) or load an image file.
2. **Segment.** Isolate the foot from the background:
   - restrict to an elliptical region of interest,
   - threshold skin tones in HSV, which is more robust to lighting changes than RGB,
   - blur and close the mask with an elliptical kernel,
   - keep the largest contour as the foot.
3. **Measure.** Locate the heel and big toe on the contour and mark the foot axis between them, the heel width (at 10% of foot length) and the widest cross-section (the metatarsal width), which are used to size the insole.
4. **Visualize.** Generate a pressure-style heatmap of the foot on a white background.
5. **Report.** Collect patient details (name, phone, foot length, insole material, delivery date) and produce a branded PDF with both feet using ReportLab.

Settings such as the last folder used and scanner options are saved per workstation with `QSettings`. The interface is in Spanish.

## Running it

```bash
pip install PyQt5 opencv-python numpy reportlab
python main.py
```

`app.py` has a `TEST_MODE` flag. With `TEST_MODE = True` (the default in this repository), the buttons load images from disk, so the app runs on any OS without a scanner. With `TEST_MODE = False` the buttons scan instead. The Windows-only WIA capture code (`pywin32`, plus an optional `pyautogui` helper that clicks through legacy scanner dialogs) is commented out in `scanner.py` so the app runs on Linux and macOS.

## Project structure

| File | Contents |
|---|---|
| `main.py` | Entry point |
| `app.py` | Main window, image loading and scanning, report workflow |
| `image_processing.py` | Segmentation, measurements and heatmap |
| `pdf_report.py` | PDF report layout |
| `ui_components.py` | Patient information dialogs |
| `scanner.py` | Scanner capture (WIA, Windows) |
| `utils.py` | Font loading and helpers |
| `resources/` | Logos, backgrounds and fonts |

## Tech

Python, PyQt5, OpenCV, NumPy, ReportLab.

More on the project: [marcossaade.github.io/orthopedics](https://marcossaade.github.io/orthopedics)
