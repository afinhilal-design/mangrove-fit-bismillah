"""Audit every source and run eligible, separately defined research tasks."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mangrove_fit.config import ROOT
from mangrove_fit.data_audit import audit_sources
from mangrove_fit.research_datasets import build_tasks
from mangrove_fit.research_ml import train_research


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'models/experiments/all_data_v2')
    args = parser.parse_args()
    out = args.out
    if any((out / name).exists() for name in ('presence_expanded', 'q4_survival_expanded', 'q3_survival_conditional', 'q2_propagule_presence')):
        parser.error('Eksperimen sudah ada; pilih folder --out baru.')
    sources = audit_sources(ROOT / 'datamangroveit', out / 'audit')
    summary = {'files_audited': len(sources), 'experiments': {}}
    for name, (frame, numeric, categorical, baseline, description) in build_tasks(ROOT / 'datamangroveit', out).items():
        print('TRAIN', name, len(frame), 'rows', frame.group.nunique(), 'groups', flush=True)
        card = train_research(frame, numeric, categorical, baseline, description, out / name)
        summary['experiments'][name] = {'rows': card['rows'], 'groups': card['groups'], 'metrics': card['metrics']}
        print(name, json.dumps(card['metrics']), flush=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
