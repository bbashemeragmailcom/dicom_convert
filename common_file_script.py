import os
import shutil

SOURCE_DIR = r"dicom_series_folder"
DEST_DIR = r"output_png"

os.makedirs(DEST_DIR, exist_ok=True)

print("Source exists:", os.path.exists(SOURCE_DIR))
print("Destination:", os.path.abspath(DEST_DIR))


def get_unique_filename(dest_dir, filename, index):
    """
    If filename already exists, append _{index}
    Example:
        image.png -> image_15.png
    """
    base, ext = os.path.splitext(filename)

    if not os.path.exists(os.path.join(dest_dir, filename)):
        return filename

    return f"{base}_{index}{ext}"


total_files = 0
processed_folders = 0

for root, dirs, files in os.walk(SOURCE_DIR):

    folder_name = os.path.basename(root)

    # Only process folders containing "-Ische"
    if "Haem" not in folder_name:
        continue

    processed_folders += 1
    print(f"\nProcessing folder: {root}")

    png_files = [f for f in files if f.lower().endswith(".png")]

    for file in png_files:

        source_file = os.path.join(root, file)

        unique_name = get_unique_filename(
            DEST_DIR,
            file,
            total_files
        )

        destination_file = os.path.join(
            DEST_DIR,
            unique_name
        )

        shutil.copy2(source_file, destination_file)

        total_files += 1

        print(
            f"Processed file {total_files}: "
            f"{file} -> {unique_name}"
        )

print(f"\nFolders processed: {processed_folders}")
print(f"Total PNG files copied: {total_files}")