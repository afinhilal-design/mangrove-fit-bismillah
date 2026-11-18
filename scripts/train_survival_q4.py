"""Train an offline Q4 survival candidate from month 0 to month 16."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mangrove_fit.config import ROOT
from mangrove_fit.survival_training import prepare_survival
from mangrove_fit.training import train_candidate, approval_blockers
from mangrove_fit.training_report import export_candidate_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'models/experiments/q4_survival_baseline')
    args = parser.parse_args()
    out = args.out
    if out.exists():
        parser.error('Folder keluaran sudah ada; gunakan --out baru.')
    prepare_survival(ROOT / 'datamangroveit/Q4_EMR-and-planting.csv', out)
    card = train_candidate(out / 'training.csv', 'seedling_survival_16_month',
                           ['sediment_level_cm'], 'blok', out, seed=42, num_rounds=100,
                           params={'nthread': 2}, manifest=out / 'dataset_manifest.json')
    report = export_candidate_report(out)
    summary = {'status': card['status'], 'metrics': card['metrics'], 'shap': report,
               'automatic_approval_blockers': approval_blockers(card, out)}
    (out / 'run_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
