import os
import numpy as np
import pydicom
import cv2
from glob import glob


# -----------------------------
# CONFIG
# -----------------------------
INPUT_DIR = "dicom_series_folder"
OUTPUT_DIR = "output_png"
SLICE_THICKNESS_FILTER = True  # optional filtering
WINDOW_CENTER = 40
WINDOW_WIDTH = 80


# -----------------------------
# LOAD DICOM SERIES
# -----------------------------
def load_dicom_series(path):
    files = glob(os.path.join(path, "*"))
    slices = [pydicom.dcmread(f) for f in files]

    def sort_key(s):
        # 1. Best option: spatial ordering
        if hasattr(s, "ImagePositionPatient"):
            return float(s.ImagePositionPatient[2])

        # 2. Fallback: InstanceNumber (safe access)
        if hasattr(s, "InstanceNumber"):
            return int(s.InstanceNumber)

        # 3. Last fallback: AcquisitionNumber if available
        if hasattr(s, "AcquisitionNumber"):
            return int(s.AcquisitionNumber)

        # 4. Worst case: keep file order stable
        return 0

    slices.sort(key=sort_key)

    return slices


# -----------------------------
# CONVERT TO HOUNSFIELD UNITS
# -----------------------------
def dicom_to_hu(dicom_slice):
    image = dicom_slice.pixel_array.astype(np.float32)

    intercept = dicom_slice.RescaleIntercept if "RescaleIntercept" in dicom_slice else 0.0
    slope = dicom_slice.RescaleSlope if "RescaleSlope" in dicom_slice else 1.0

    hu_image = image * slope + intercept
    return hu_image


# -----------------------------
# WINDOWING FUNCTION
# -----------------------------
def window_image(image, center, width):
    lower = center - width // 2
    upper = center + width // 2

    image = np.clip(image, lower, upper)
    image = (image - lower) / (upper - lower)
    image = (image * 255).astype(np.uint8)

    return image

# -----------------------------
# PRESERVE DICOM WINDOW
# -----------------------------
def get_window_values(ds):
    center = getattr(ds, "WindowCenter", None)
    width = getattr(ds, "WindowWidth", None)

    # Some DICOMs store these as lists
    if isinstance(center, pydicom.multival.MultiValue):
        center = float(center[0])

    if isinstance(width, pydicom.multival.MultiValue):
        width = float(width[0])

    return center, width


def dicom_window_image(hu_image, s):
    center, width = get_window_values(s)
    if center is not None and width is not None:
        png_image = window_image(hu_image, center, width)
    else:
        # Fallback: simple min-max normalization
        img = hu_image.astype(np.float32)
        img = (img - img.min()) / (img.max() - img.min())
        png_image = (img * 255).astype(np.uint8)
    return png_image

# -----------------------------
# SAVE PNG
# -----------------------------
def save_png(image, out_path):
    cv2.imwrite(out_path, image)


# -----------------------------
# MAIN PROCESSING PIPELINE
# -----------------------------
def process_single_series(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    slices = load_dicom_series(input_dir)

    print(f"Loaded {len(slices)} slices")

    for i, s in enumerate(slices):
        try:
            hu_image = dicom_to_hu(s)
            # png_image = window_image(hu_image, WINDOW_CENTER, WINDOW_WIDTH)
            png_image = dicom_window_image(hu_image, s)

            out_file = os.path.join(output_dir, f"slice_{i:04d}.png")
            save_png(png_image, out_file)

        except Exception as e:
            print(f"Skipping slice {i}: {e}")

    print("Conversion complete.")

# -----------------------------
# PROCESS ALL SUBFOLDERS
# -----------------------------
def process_all_series(input_root, output_root):
    os.makedirs(output_root, exist_ok=True)

    subfolders = [
        os.path.join(input_root, d)
        for d in os.listdir(input_root)
        if os.path.isdir(os.path.join(input_root, d))
    ]

    print(f"Found {len(subfolders)} series folders")

    for folder in subfolders:
        folder_name = os.path.basename(folder)

        output_folder = os.path.join(
            output_root,
            f"{folder_name}_png"
        )

        process_single_series(folder, output_folder)

    print("All conversions complete.")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    process_all_series(INPUT_DIR, OUTPUT_DIR)