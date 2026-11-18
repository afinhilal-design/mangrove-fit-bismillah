"""Train the natural seedling presence candidate and export native TreeSHAP.

Run: .venv/Scripts/python.exe scripts/train_datamangroveit.py
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mangrove_fit.config import ROOT
from mangrove_fit.dataset_d02 import convert_combined
from mangrove_fit.training import train_candidate, approval_blockers
from mangrove_fit.training_report import export_candidate_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'models' / 'experiments' / 'datamangroveit_presence')
    args = parser.parse_args()
    out = args.out
    if out.exists():
        parser.error('Folder keluaran sudah ada; pilih --out baru agar hasil lama tetap tersimpan.')
    source = ROOT / 'datamangroveit'
    manifest = convert_combined(source / 'sea-site_dataset_withNAs.csv',
                                source / 'pond_dataset_withNAs_UTF8.csv',
                                out / 'training.csv', out / 'dataset_manifest.json')
    # Use existing established parameters; newly added parameters still need schema review.
    features = ['inundation_duration_h_day', 'soil_ph', 'redox_mv']
    manifest['selected_features'] = features
    manifest['known_limitations'] += [
        'Target keberadaan semai alami, bukan probabilitas survival penanaman.',
        'Satuan redox dan definisi periode genangan perlu konfirmasi metadata sumber.',
        'Validasi memakai transek; independensi geografis antartransek belum dibuktikan.',
        'Q4 tidak digunakan: konversi lama memakai sedimen akhir dan groupby.last yang dapat mengisi NA dari bulan sebelumnya.',
        'Berkas batimetri dan deret waktu tidak digabung tanpa kunci lokasi/waktu yang terverifikasi.',
    ]
    (out / 'dataset_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    card = train_candidate(out / 'training.csv', 'seedling_presence', features, 'blok', out,
                           seed=42, num_rounds=100, params={'nthread': 2}, manifest=out / 'dataset_manifest.json')
    report = export_candidate_report(out)
    summary = {'model_status': card['status'], 'metrics': card['metrics'], 'shap': report,
               'automatic_approval_blockers': approval_blockers(card, out)}
    (out / 'run_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
