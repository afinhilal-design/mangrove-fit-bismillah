"""Setujui kandidat model dan pasang ke models/active (tindakan peninjau ahli).

Contoh:
  python scripts/approve_model.py --reviewer "Nama Peninjau" --note "Diuji pada blok uji independen"

Ditolak bila kandidat sintetis, checksum tidak cocok, atau balanced accuracy uji tidak
melampaui baseline. Model aktif lama diarsipkan ke models/archive/<versi>/.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mangrove_fit.training import approve_candidate, TrainingError  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--reviewer', required=True)
    ap.add_argument('--note', default='')
    a = ap.parse_args(argv)
    try:
        card = approve_candidate(a.reviewer, a.note)
    except TrainingError as exc:
        print('DITOLAK:', exc, file=sys.stderr)
        return 2
    print(f"Model {card['version']} disetujui oleh {card['approved_by']} dan kini aktif.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
