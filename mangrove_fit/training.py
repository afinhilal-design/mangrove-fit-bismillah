"""Pipeline pelatihan XGBoost -> kandidat model (belum aktif).

Alur:
  1. train_candidate()   : CSV berlabel -> models/candidate/{model.ubj, model_card.json}
                           status PENDING_REVIEW (atau SYNTHETIC_TEST_ONLY untuk data sintetis).
  2. approve_candidate() : peninjau ahli menyetujui -> disalin ke models/active/ dengan status APPROVED.

Prinsip (lihat AGENTS.md dan models/README.md):
  - Tidak ada imputasi: baris dengan fitur/label kosong dibuang dan jumlahnya dicatat.
  - Pembagian train/validation/test berbasis blok spasial (seluruh blok masuk satu bagian),
    sehingga lokasi uji tidak pernah terlihat saat pelatihan.
  - Domain penerapan = rentang min/maks fitur pada data latih; di luar itu prediksi ditolak.
  - Data sintetis boleh dipakai untuk menguji kode, tetapi kartunya tidak pernah bisa disetujui.
  - Model disimpan dalam format native UBJ (bukan pickle).
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ROOT, MODEL_DIR
from .schemas import PARAMETERS

CANDIDATE_DIR = ROOT / 'models' / 'candidate'
ARCHIVE_DIR = ROOT / 'models' / 'archive'
NUMERIC_FEATURES = [k for k, m in PARAMETERS.items() if m['unit'] != 'kategori']
MIN_ROWS = 40
MIN_BLOCKS = 4
DEFAULT_PARAMS = {
    'objective': 'binary:logistic', 'eval_metric': 'logloss', 'max_depth': 3, 'eta': 0.08,
    'subsample': 0.9, 'colsample_bytree': 0.9, 'min_child_weight': 2, 'lambda': 1.0,
}


class TrainingError(ValueError):
    """Kesalahan yang dapat ditindaklanjuti pengguna (pesan Bahasa Indonesia)."""


# --------------------------------------------------------------------------- data

def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def looks_synthetic(path: Path, frame: pd.DataFrame) -> bool:
    """Data demo/sintetis dikenali dari lokasi, nama berkas, atau kolom penanda."""
    path = Path(path).resolve()
    demo_dir = (ROOT / 'data' / 'demo').resolve()
    if demo_dir in path.parents or 'SYNTHETIC' in path.name.upper():
        return True
    if 'is_demo' in frame.columns and frame['is_demo'].astype(str).str.lower().isin(['1', 'true']).any():
        return True
    if 'quality_flag' in frame.columns and (frame['quality_flag'].astype(str).str.lower() == 'demo').any():
        return True
    return False


def load_training_table(path, target: str, features: list[str], block_col: str):
    """Baca CSV, validasi kolom & label, buang baris tidak lengkap (tanpa imputasi)."""
    path = Path(path)
    if not path.exists():
        raise TrainingError(f'Berkas {path} tidak ditemukan.')
    frame = pd.read_csv(path)
    unknown = [f for f in features if f not in NUMERIC_FEATURES]
    if unknown:
        raise TrainingError('Fitur bukan parameter numerik MANGROVE-FIT: ' + ', '.join(unknown)
                            + '. Fitur yang didukung: ' + ', '.join(NUMERIC_FEATURES) + '.')
    absent = [c for c in [target, block_col, *features] if c not in frame.columns]
    if absent:
        raise TrainingError('Kolom tidak ada di CSV: ' + ', '.join(absent) + '.')
    for f in features:
        frame[f] = pd.to_numeric(frame[f], errors='coerce')
    labels = pd.to_numeric(frame[target], errors='coerce')
    bad = labels.notna() & ~labels.isin([0, 1])
    if bad.any():
        raise TrainingError(f'Label {target} harus biner 0/1; ditemukan nilai lain pada {int(bad.sum())} baris.')
    frame[target] = labels
    before = len(frame)
    frame = frame.dropna(subset=[target, block_col, *features]).copy()
    frame[target] = frame[target].astype(int)
    frame[block_col] = frame[block_col].astype(str)
    return frame, before - len(frame)


def spatial_block_split(frame: pd.DataFrame, block_col: str, test_frac=0.25, val_frac=0.2, seed=42, label_col=None):
    """Bagi per blok spasial utuh. Mengembalikan dict nama_bagian -> daftar blok.

    Bila label_col diberikan, blok yang memuat kelas positif dan blok tanpa positif dibagi
    terpisah (stratifikasi tingkat blok), agar setiap bagian berpeluang memuat kedua kelas.
    """
    blocks = np.array(sorted(frame[block_col].unique()))
    if len(blocks) < MIN_BLOCKS:
        raise TrainingError(f'Minimal {MIN_BLOCKS} blok spasial diperlukan agar uji lokasi independen; ditemukan {len(blocks)}.')
    rng = np.random.default_rng(seed)
    if label_col is None:
        groups = [blocks]
    else:
        pos = set(frame.loc[frame[label_col] == 1, block_col])
        groups = [np.array([b for b in blocks if b in pos]), np.array([b for b in blocks if b not in pos])]
    out = {'test': [], 'validation': [], 'train': []}
    for g in groups:
        g = g.copy(); rng.shuffle(g)
        if len(g) >= 3:
            n_test = max(1, round(len(g) * test_frac)); n_val = max(1, round(len(g) * val_frac))
        else:  # kelompok kecil: utamakan data latih
            n_test, n_val = (1, 0) if len(g) == 2 else (0, 0)
        out['test'] += g[:n_test].tolist(); out['validation'] += g[n_test:n_test + n_val].tolist()
        out['train'] += g[n_test + n_val:].tolist()
    return {k: sorted(v) for k, v in out.items()}


def leave_one_block_out(frame, target, features, block_col, params, num_rounds) -> dict:
    """Validasi silang: setiap blok diprediksi oleh model yang dilatih tanpa blok tersebut."""
    import xgboost as xgb
    ys, ps, skipped = [], [], []
    for b in sorted(frame[block_col].unique()):
        tr, te = frame[frame[block_col] != b], frame[frame[block_col] == b]
        if tr[target].nunique() < 2:
            skipped.append(b); continue
        booster = xgb.train(params, xgb.DMatrix(tr[features].to_numpy(float), label=tr[target].to_numpy(int), feature_names=features), num_boost_round=num_rounds)
        ps += booster.predict(xgb.DMatrix(te[features].to_numpy(float), feature_names=features)).tolist()
        ys += te[target].astype(int).tolist()
    m = classification_metrics(ys, ps)
    m['baseline_pr_auc'] = round(float(np.mean(ys)), 4) if ys else None
    m['blocks_skipped'] = skipped
    return m


# ------------------------------------------------------------------------ metrics

def classification_metrics(y_true, prob, threshold=0.5) -> dict:
    """Balanced accuracy, F1, PR-AUC (average precision), Brier. Tanpa scikit-learn."""
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(prob, dtype=float)
    pred = (p >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
    fp = int(((pred == 1) & (y == 0)).sum()); fn = int(((pred == 0) & (y == 1)).sum())
    tpr = tp / (tp + fn) if tp + fn else None
    tnr = tn / (tn + fp) if tn + fp else None
    bal = (tpr + tnr) / 2 if tpr is not None and tnr is not None else None
    prec = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * prec * tpr / (prec + tpr) if tpr and prec + tpr else 0.0
    # Average precision at distinct thresholds; tied scores enter together.
    order = np.argsort(-p, kind='mergesort')
    ys = y[order]
    n_pos = int(ys.sum())
    ends = np.r_[np.flatnonzero(np.diff(p[order])), len(y) - 1] if len(y) else np.array([], dtype=int)
    cumulative_tp = np.cumsum(ys)[ends]
    ap = float(np.sum(np.diff(np.r_[0, cumulative_tp]) * cumulative_tp / (ends + 1)) / n_pos) if n_pos else None
    r = lambda v: None if v is None else round(float(v), 4)
    return {'n': int(len(y)), 'prevalence': r(y.mean()) if len(y) else None, 'balanced_accuracy': r(bal),
            'f1': r(f1), 'pr_auc': r(ap), 'brier': r(((p - y) ** 2).mean()) if len(y) else None,
            'confusion': {'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn}, 'threshold': threshold}


# ----------------------------------------------------------------------- training

def train_candidate(path, target: str, features: list[str], block_col: str, out_dir=None, *,
                    seed=42, num_rounds=400, allow_synthetic=False, params=None, manifest=None) -> dict:
    """Latih XGBoost dan tulis kandidat model. Mengembalikan isi model_card."""
    import xgboost as xgb  # impor malas: dependensi opsional (requirements-ml.txt)

    path = Path(path)
    out_dir = Path(out_dir or CANDIDATE_DIR)
    raw = pd.read_csv(path) if path.exists() else pd.DataFrame()
    synthetic = looks_synthetic(path, raw)
    if synthetic and not allow_synthetic:
        raise TrainingError('Dataset terdeteksi sintetis/demo. Model dari data ini tidak boleh dipakai; '
                            'gunakan allow_synthetic hanya untuk menguji kode.')
    frame, dropped = load_training_table(path, target, features, block_col)
    if len(frame) < MIN_ROWS:
        raise TrainingError(f'Hanya {len(frame)} baris lengkap; minimal {MIN_ROWS} baris berlabel diperlukan.')

    split = spatial_block_split(frame, block_col, seed=seed, label_col=target)
    parts = {name: frame[frame[block_col].isin(blocks)] for name, blocks in split.items()}
    for name, part in parts.items():
        if part[target].nunique() < 2:
            raise TrainingError(f'Bagian {name} hanya berisi satu kelas label; tambah data atau blok spasial.')

    def dmatrix(part):
        return xgb.DMatrix(part[features].to_numpy(float), label=part[target].to_numpy(int), feature_names=features)

    dtrain, dval, dtest = dmatrix(parts['train']), dmatrix(parts['validation']), dmatrix(parts['test'])
    run_params = {**DEFAULT_PARAMS, **(params or {}), 'seed': seed}
    booster = xgb.train(run_params, dtrain, num_boost_round=num_rounds, evals=[(dval, 'validation')],
                        early_stopping_rounds=30, verbose_eval=False)
    best = int(booster.best_iteration)
    booster = booster[: best + 1]  # simpan hanya pohon sampai iterasi terbaik

    def evaluate(dm, part):
        return classification_metrics(part[target], booster.predict(dm))

    # Baseline: prevalensi kelas positif di data latih untuk semua baris.
    base_p = float(parts['train'][target].mean())
    metrics = {
        'baseline_prevalence': {k: classification_metrics(v[target], np.full(len(v), base_p)) for k, v in
                                (('validation', parts['validation']), ('test', parts['test']))},
        'train': evaluate(dtrain, parts['train']),
        'validation': evaluate(dval, parts['validation']),
        'test': evaluate(dtest, parts['test']),
        # Fixed budget, independent of validation/test labels in outer folds.
        'cv_leave_one_block_out': leave_one_block_out(frame, target, features, block_col, run_params, num_rounds),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / 'model.ubj'
    booster.save_model(str(model_path))
    train_part = parts['train']
    card = {
        'status': 'SYNTHETIC_TEST_ONLY' if synthetic else 'PENDING_REVIEW',
        'synthetic': synthetic,
        'version': f"cand-{datetime.now(timezone.utc):%Y%m%d}-{_sha256(model_path)[:8]}",
        'target': target,
        'features': list(features),
        'sha256': _sha256(model_path),
        'domain': {f: [float(train_part[f].min()), float(train_part[f].max())] for f in features},
        'output_space': 'probability',
        'approved_by': None,
        'training': {
            'data_file': path.name, 'data_sha256': _sha256(path), 'rows_used': int(len(frame)),
            'rows_dropped_incomplete': int(dropped), 'block_column': block_col, 'blocks': split,
            'rows_per_split': {k: int(len(v)) for k, v in parts.items()},
            'split_strategy': 'blok spasial utuh, distratifikasi menurut keberadaan kelas positif per blok',
            'dataset_manifest': json.loads(Path(manifest).read_text(encoding='utf-8')) if manifest else None,
            'params': run_params, 'best_iteration': best, 'cv_num_rounds': num_rounds, 'xgboost_version': xgb.__version__,
            'trained_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        },
        'metrics': metrics,
    }
    (out_dir / 'model_card.json').write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding='utf-8')
    return card


# ----------------------------------------------------------------------- approval

def read_card(model_dir) -> dict | None:
    p = Path(model_dir) / 'model_card.json'
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except ValueError:
        return None


def approval_blockers(card: dict, candidate_dir=None) -> list[str]:
    """Daftar alasan kandidat belum dapat disetujui (kosong = boleh ditinjau untuk disetujui)."""
    out = []
    if card.get('synthetic') or card.get('status') == 'SYNTHETIC_TEST_ONLY':
        out.append('Kandidat dilatih dari data sintetis; tidak dapat disetujui.')
    elif card.get('status') != 'PENDING_REVIEW':
        out.append(f"Status kandidat {card.get('status')} tidak dapat disetujui.")
    if candidate_dir is not None and (not (Path(candidate_dir) / 'model.ubj').exists() or _sha256(Path(candidate_dir) / 'model.ubj') != card.get('sha256')):
        out.append('Checksum model.ubj kandidat tidak cocok dengan kartunya.')
    m = card.get('metrics', {})
    test, base = m.get('test', {}), m.get('baseline_prevalence', {}).get('test', {})
    if test.get('balanced_accuracy') is None or test['balanced_accuracy'] <= (base.get('balanced_accuracy') or 0.5):
        out.append(f"Balanced accuracy uji ({test.get('balanced_accuracy')}) tidak melampaui baseline ({base.get('balanced_accuracy')}).")
    cv = m.get('cv_leave_one_block_out')
    if cv and (cv.get('balanced_accuracy') is None or cv['balanced_accuracy'] <= 0.5):
        out.append(f"Validasi silang antar-blok tidak lebih baik dari tebakan acak (balanced accuracy {cv.get('balanced_accuracy')}).")
    return out


def approve_candidate(reviewer: str, note: str = '', candidate_dir=None, active_dir=None, archive_dir=None) -> dict:
    """Setujui kandidat dan pasang ke models/active. Model aktif lama diarsipkan, bukan dihapus."""
    candidate_dir = Path(candidate_dir or CANDIDATE_DIR)
    active_dir = Path(active_dir or MODEL_DIR)
    card = read_card(candidate_dir)
    if card is None:
        raise TrainingError('Tidak ada kandidat model. Jalankan scripts/train_model.py dahulu.')
    if not reviewer or not reviewer.strip():
        raise TrainingError('Nama peninjau wajib diisi.')
    blockers = approval_blockers(card, candidate_dir)
    if blockers:
        raise TrainingError(blockers[0] + ' Model tidak layak disetujui.')

    if (active_dir / 'model_card.json').exists():
        old = read_card(active_dir) or {}
        dest = Path(archive_dir or ARCHIVE_DIR) / str(old.get('version', 'tanpa-versi'))
        dest.mkdir(parents=True, exist_ok=True)
        for name in ('model.ubj', 'model_card.json'):
            if (active_dir / name).exists():
                shutil.copy2(active_dir / name, dest / name)
    active_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate_dir / 'model.ubj', active_dir / 'model.ubj')
    card.update(status='APPROVED', approved_by=reviewer.strip(), approval_note=note,
                approved_at=datetime.now(timezone.utc).isoformat(timespec='seconds'))
    (active_dir / 'model_card.json').write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding='utf-8')
    return card
