"""Konversi dataset D02 (sea-site + pond gabungan) dan D03 (Q4 planting survival).

Contoh:
  python scripts/convert_datasets.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mangrove_fit.dataset_d02 import convert_combined, TRAIN_CSV as D02_CSV, MANIFEST as D02_MANIFEST  # noqa: E402
from mangrove_fit.dataset_d03 import convert_q4, TRAIN_CSV as D03_CSV, MANIFEST as D03_MANIFEST  # noqa: E402
from mangrove_fit.config import ROOT  # noqa: E402


def main():
    data_dir = ROOT / 'datamangroveit'

    # --- D02: Combined sea-site + pond ---
    sea_site_path = data_dir / 'sea-site_dataset_withNAs.csv'
    pond_path = data_dir / 'pond_dataset_withNAs_UTF8.csv'
    print('=== Konversi D02: Combined sea-site + pond ===')
    if not sea_site_path.exists():
        print(f'GAGAL: {sea_site_path} tidak ditemukan.', file=sys.stderr)
        return 1
    if not pond_path.exists():
        print(f'GAGAL: {pond_path} tidak ditemukan.', file=sys.stderr)
        return 1
    m2 = convert_combined(sea_site_path, pond_path)
    print(f"  Berkas: {D02_CSV}")
    print(f"  Baris: {m2['rows']} (sea: {m2['rows_per_zone']['sea']}, pond: {m2['rows_per_zone']['pond']})")
    print(f"  Blok: {m2['blocks']}")
    print(f"  Target: {m2['target']['positives']} positif / {m2['target']['negatives']} negatif")
    print(f"  Manifest: {D02_MANIFEST}")
    print()

    # --- D03: Q4 planting survival ---
    q4_path = data_dir / 'Q4_EMR-and-planting.csv'
    print('=== Konversi D03: Q4 planting survival ===')
    if not q4_path.exists():
        print(f'GAGAL: {q4_path} tidak ditemukan.', file=sys.stderr)
        return 1
    m3 = convert_q4(q4_path)
    print(f"  Berkas: {D03_CSV}")
    print(f"  Baris: {m3['rows']} (bibit unik: {m3['unique_seedlings']})")
    print(f"  Blok: {m3['blocks']}")
    print(f"  Target: {m3['target']['positives']} positif / {m3['target']['negatives']} negatif")
    print(f"  Spesies: {m3['species_distribution']}")
    print(f"  Manifest: {D03_MANIFEST}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
