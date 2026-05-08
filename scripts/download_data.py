# ============================================================
# download_data.py  —  Phase 2
# Downloads raw patent data files from USPTO PatentsView
# ============================================================

import os
import requests
from tqdm import tqdm

# Output folder
RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
os.makedirs(RAW_DIR, exist_ok=True)

# PatentsView bulk data files to download
FILES = {
    "patent.tsv.zip":          "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/patent.tsv.zip",
    "inventor.tsv.zip":        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/inventor.tsv.zip",
    "assignee.tsv.zip":        "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/assignee.tsv.zip",
    "patent_inventor.tsv.zip": "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/patent_inventor.tsv.zip",
    "patent_assignee.tsv.zip": "https://data.uspto.gov/bulkdata/datasets/pvgpatdis/patent_assignee.tsv.zip",
}


def download_file(url, dest_path):
    """Download a file with a progress bar."""
    print(f"\nDownloading: {os.path.basename(dest_path)}")
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    total = int(response.headers.get('content-length', 0))
    with open(dest_path, 'wb') as f, tqdm(total=total, unit='B', unit_scale=True) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))
    print(f"  Saved to: {dest_path}")


def main():
    print("=" * 55)
    print("  USPTO PatentsView — Data Downloader")
    print("=" * 55)
    print(f"Saving files to: {os.path.abspath(RAW_DIR)}\n")

    for filename, url in FILES.items():
        dest = os.path.join(RAW_DIR, filename)
        if os.path.exists(dest):
            print(f"  Already exists, skipping: {filename}")
        else:
            try:
                download_file(url, dest)
            except Exception as e:
                print(f"  ERROR downloading {filename}: {e}")
                print("  Visit https://data.uspto.gov/bulkdata/datasets/pvgpatdis")
                print("  and download it manually into data/raw/")

    print("\n  All downloads complete.")
    print("  Next step: run  python scripts/clean_data.py")


if __name__ == "__main__":
    main()