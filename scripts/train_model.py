"""Latih kandidat model XGBoost dari CSV berlabel.

Contoh:
  python scripts/train_model.py data/latih.csv --target habitat_present \
      --features salinity_ppt inundation_duration_h_day elevation_m ndvi --block-col blok_pesisir

CSV wajib berisi kolom target (0/1), kolom blok spasial, dan kolom fitur numerik
(nama parameter MANGROVE-FIT). Hasil: models/candidate/ dengan status PENDING_REVIEW.
Model kandidat BELUM aktif; setujui dengan scripts/approve_model.py.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mangrove_fit.training import train_candidate, TrainingError, NUMERIC_FEATURES  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--target', required=True, help='kolom label biner 0/1')
    ap.add_argument('--features', nargs='+', required=True, help='pilihan: ' + ', '.join(NUMERIC_FEATURES))
    ap.add_argument('--block-col', required=True, help='kolom ID blok spasial untuk pembagian train/val/test')
    ap.add_argument('--out', default=None, help='folder keluaran (bawaan models/candidate)')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--manifest', default=None, help='manifest dataset (JSON) yang ikut dicatat di kartu model')
    ap.add_argument('--allow-synthetic', action='store_true', help='izinkan data sintetis HANYA untuk uji kode')
    a = ap.parse_args(argv)
    try:
        card = train_candidate(a.csv, a.target, a.features, a.block_col, a.out, seed=a.seed, allow_synthetic=a.allow_synthetic, manifest=a.manifest)
    except TrainingError as exc:
        print('GAGAL:', exc, file=sys.stderr)
        return 2
    except ImportError:
        print('GAGAL: paket xgboost belum terpasang. Jalankan: pip install -r requirements-ml.txt', file=sys.stderr)
        return 2
    m = card['metrics']
    print(f"Kandidat {card['version']} · status {card['status']}")
    print(f"Baris dipakai {card['training']['rows_used']} · dibuang (tidak lengkap) {card['training']['rows_dropped_incomplete']}")
    for name in ('validation', 'test'):
        print(f"{name:>10}: " + json.dumps({k: m[name][k] for k in ('n', 'balanced_accuracy', 'f1', 'pr_auc', 'brier')})
              + f"  | baseline BA {m['baseline_prevalence'][name]['balanced_accuracy']}")
    cv = m['cv_leave_one_block_out']
    print(f"  cv-blok: n={cv['n']} balanced_accuracy={cv['balanced_accuracy']} pr_auc={cv['pr_auc']} (baseline PR-AUC {cv['baseline_pr_auc']})")
    if card['status'] == 'SYNTHETIC_TEST_ONLY':
        print('PERINGATAN: data sintetis — kandidat ini tidak akan pernah bisa disetujui.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
