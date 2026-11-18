"""Impor dataset D01 sea-site (Demak) menjadi tabel latih MANGROVE-FIT.

Contoh:
  python scripts/import_sea_site.py "C:/Users/.../sea-site_dataset_withNAs.csv"
Hasil: data/raw/D01/ (salinan asli), data/training/D01_sea_site_seedling.csv, data/manifests/D01.json
Lanjutkan dengan scripts/train_model.py (perintah dicetak di akhir).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mangrove_fit.dataset_d01 import convert_sea_site, TARGET, BLOCK, FEATURES, TRAIN_CSV, MANIFEST  # noqa: E402


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__); return 2
    try:
        m = convert_sea_site(argv[0])
    except (OSError, ValueError) as exc:
        print('GAGAL:', exc, file=sys.stderr); return 2
    print(f"{m['rows']} titik, {m['blocks']} transek, {m['target']['positives']} positif ({TARGET}).")
    for k, v in m['features'].items():
        print(f"  {k:28} <- {v['source']:14} kosong: {v['missing']}")
    print('\nLatih kandidat:')
    print(f'  python scripts/train_model.py {TRAIN_CSV.relative_to(Path.cwd()) if Path.cwd() in TRAIN_CSV.parents else TRAIN_CSV} '
          f'--target {TARGET} --features {" ".join(FEATURES)} --block-col {BLOCK} --manifest {MANIFEST.as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
