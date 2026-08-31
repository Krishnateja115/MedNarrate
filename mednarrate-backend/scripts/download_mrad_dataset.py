import os
import sys
import zipfile
import urllib.request
from pathlib import Path

# ==========================================
# TODO: PASTE YOUR DIRECT DOWNLOAD LINK HERE
# ==========================================
# If using Google Drive, generate a direct download link (e.g. using a tool like https://sites.google.com/site/gdocs2direct/)
DATASET_URL = "https://example.com/path/to/MRAD_Dataset.zip"
# ==========================================

DEST_DIR = Path(__file__).parent.parent.parent / "MRAD"
ZIP_PATH = DEST_DIR.parent / "MRAD_Dataset.zip"

def download_dataset():
    if DEST_DIR.exists() and any(DEST_DIR.iterdir()):
        print("✅ MRAD dataset already exists locally. Skipping download.")
        return

    if DATASET_URL == "https://example.com/path/to/MRAD_Dataset.zip":
        print("❌ Error: You must update DATASET_URL in this script with your actual hosted link!")
        sys.exit(1)

    print(f"Downloading MRAD dataset from {DATASET_URL}...")
    try:
        # Download the file
        urllib.request.urlretrieve(DATASET_URL, ZIP_PATH)
        print("✅ Download complete. Extracting...")
        
        # Extract the zip file
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(DEST_DIR.parent)
            
        print("✅ Extraction complete. Cleaning up...")
        os.remove(ZIP_PATH)
        print("🎉 Dataset successfully installed into the MRAD/ directory!")
        
    except Exception as e:
        print(f"❌ Failed to download or extract the dataset: {e}")
        if ZIP_PATH.exists():
            os.remove(ZIP_PATH)
        sys.exit(1)

if __name__ == "__main__":
    download_dataset()
