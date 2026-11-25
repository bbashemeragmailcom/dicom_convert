import os
import re

ROOT_DIR = "dicom_series_folder"

def clean_name(name):
    # remove _png and replace spaces with underscores
    return name.replace("_png", "").replace(" ", "_")

for root, dirs, files in os.walk(ROOT_DIR):
    folder_name = os.path.basename(root)

    if folder_name.endswith("_png"):
        prefix = clean_name(folder_name)

        for f in files:
            if f.lower().endswith(".png"):
                old_path = os.path.join(root, f)

                # extract number if exists (slice_0001.png -> 0001)
                match = re.search(r"(\d+)", f)
                num = match.group(1) if match else "000"

                new_name = f"{prefix}_{num}.png"
                new_path = os.path.join(root, new_name)

                print(f"Renaming: {f} → {new_name}")
                os.rename(old_path, new_path)

print("Done.")