"""Build provenance and a static comparison figure from completed research results."""
import importlib.metadata
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'models/experiments/all_data_v2'
SOURCES = {
    'presence_expanded': ['sea-site_dataset_withNAs.csv', 'pond_dataset_withNAs_UTF8.csv'],
    'q4_survival_expanded': ['Q4_EMR-and-planting.csv'],
    'q3_survival_conditional': ['Q3_EMR-dams_seedling_survival_exp.csv'],
    'q2_propagule_presence': ['Q2_EMR-hydrology_propagules.csv'],
}


def main():
    audit = json.loads((BASE / 'audit/source_audit.json').read_text(encoding='utf-8'))
    indexed = {r['file']: r for r in audit}
    for name, files in SOURCES.items():
        manifest = {'source_files': [{'file': f, 'sha256': indexed[f]['sha256']} for f in files],
                    'audit': '../audit/source_audit.json', 'preparation': '../preparation.json',
                    'scenario_data_used_in_training': False,
                    'historical_dates_and_locations_preserved': True}
        (BASE / name / 'source_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    versions = {p: importlib.metadata.version(p) for p in ['xgboost', 'scikit-learn', 'pandas', 'numpy', 'openpyxl']}
    (BASE / 'environment.json').write_text(json.dumps(versions, indent=2), encoding='utf-8')
    summary = json.loads((BASE / 'summary.json').read_text(encoding='utf-8'))
    names = list(SOURCES)
    labels = ['Semai alami', 'Survival Q4\n0 ke 16 bulan', 'Survival Q3\n3 ke 10 bulan', 'Propagul Q2']
    fixed = [summary['experiments'][n]['metrics']['nested_oof_threshold_05']['balanced_accuracy'] for n in names]
    tuned = [summary['experiments'][n]['metrics']['nested_oof_tuned_threshold']['balanced_accuracy'] for n in names]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1.45, 1]})
    import numpy as np
    x = np.arange(len(names))
    axes[0].bar(x - 0.18, fixed, width=0.36, color='#286b5c', label='Ambang tetap 0,5')
    axes[0].bar(x + 0.18, tuned, width=0.36, color='#b89145', label='Ambang dipilih di validasi internal')
    axes[0].axhline(0.5, color='#555555', linestyle='--', linewidth=1)
    axes[0].set_xticks(x, labels)
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel('Balanced accuracy validasi silang luar')
    axes[0].set_title('Empat target berbeda; bukan satu skor keberhasilan')
    axes[0].legend(loc='upper left', fontsize=8)
    shap = pd.read_csv(BASE / 'q4_survival_expanded/shap_importance.csv').iloc[::-1]
    mapping = {'species': 'Spesies', 'length': 'Ukuran bibit awal', 'sediment_level_cm': 'Sedimen awal'}
    axes[1].barh(shap.feature.map(mapping), shap.mean_abs_oof_shap_log_odds, color='#286b5c')
    axes[1].set_title('SHAP survival Q4 pada observasi uji tiap fold')
    axes[1].set_xlabel('Rata-rata |SHAP|, log-odds')
    fig.suptitle('MANGROVE-FIT | Evaluasi riset data historis', fontsize=15)
    fig.text(0.5, 0.02, 'RESEARCH_ONLY - bukan validasi lapangan terkini; SHAP bukan hubungan sebab-akibat.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    fig.savefig(BASE / 'research_comparison.png', dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
