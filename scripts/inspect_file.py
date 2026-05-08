# ============================================================
# inspect_columns.py
# Run this BEFORE clean_data.py
# It reads the first row of every file in data/raw/ and
# prints the column names so we know exactly what to clean
# ============================================================

import os
import zipfile

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')


def get_header(filepath):
    """Get the header line from a TSV or zipped TSV."""
    if filepath.endswith('.zip'):
        with zipfile.ZipFile(filepath, 'r') as z:
            name = z.namelist()[0]
            with z.open(name) as f:
                header = f.readline().decode('utf-8').strip()
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            header = f.readline().strip()
    return header


def main():
    print("=" * 60)
    print("  Column Inspector — data/raw/")
    print("=" * 60)

    files = sorted([
        f for f in os.listdir(RAW_DIR)
        if f.endswith('.tsv') or f.endswith('.tsv.zip') or f.endswith('.zip')
    ])

    if not files:
        print("  No files found in data/raw/")
        print(f"  Looking in: {os.path.abspath(RAW_DIR)}")
        return

    for filename in files:
        filepath = os.path.join(RAW_DIR, filename)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"\n FILE: {filename}  ({size_mb:.1f} MB)")
        try:
            header = get_header(filepath)
            cols = [c.strip().strip('"') for c in header.split('\t')]
            for i, col in enumerate(cols):
                print(f"   [{i}] {col}")
        except Exception as e:
            print(f"   ERROR reading file: {e}")

    print("\n" + "=" * 60)
    print("  Copy this output and share it — then clean_data.py")
    print("  will be written to match your exact column names.")
    print("=" * 60)


if __name__ == "__main__":
    main()