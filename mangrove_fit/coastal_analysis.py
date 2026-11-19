"""Unsupervised, within-datasheet prioritisation with explicit evidence per site."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

from .config import load_rules

INDICATORS = {
    'ndvi': 'NDVI saat ini', 'delta': 'perubahan NDVI', 'piksel': 'piksel menurun',
    'tajuk': 'tutupan tajuk', 'hilang': 'kehilangan luas', 'pohon': 'kerapatan pohon',
}
MEASURES = ['ndvi', 'ndvi_sebelumnya', 'piksel_menurun_pct', 'tutupan_pct', 'kehilangan_pct',
            'luas_awal_ha', 'luas_akhir_ha', 'kerapatan', 'latitude', 'longitude']
CANDIDATE = 'Kandidat rehabilitasi'
VERIFY = 'Survei kondisi'
MONITOR = 'Pantau'
INSUFFICIENT = 'Data belum cukup'
EXCLUDED = 'Dikecualikan'
COLOURS = {EXCLUDED: '#585268', CANDIDATE: '#9d4b2d', VERIFY: '#956a22', MONITOR: '#346856', INSUFFICIENT: '#717877'}


def fmt(value, places=2):
    return f'{value:.{places}f}'.replace('.', ',')


def latest_sites(frame):
    """Median of replicates on the latest date; older dated visits may supply a baseline."""
    data = frame.copy()
    data['kabupaten_kota'] = data.get('kabupaten_kota', pd.Series('', index=data.index)).fillna('')
    data['tanggal'] = data.get('tanggal', pd.Series('', index=data.index)).fillna('').astype(str)
    rules = load_rules()
    records = []
    for (region, loc), visits in data.groupby(['kabupaten_kota', 'lokasi'], sort=False):
        when = visits['tanggal'].max()
        last = visits[visits['tanggal'] == when]
        numeric = [name for name in MEASURES if name in last.columns]
        values = last[numeric].median(numeric_only=True).dropna().to_dict()
        # Preserve an actual measured coordinate pair, never the midpoint of two sites.
        if {'longitude', 'latitude'}.issubset(last.columns):
            coords = last[['longitude', 'latitude']].dropna()
            values.pop('longitude', None)
            values.pop('latitude', None)
            if not coords.empty:
                values.update(coords.iloc[0].to_dict())
        previous = visits[(visits['tanggal'] != '') & (visits['tanggal'] < when)]
        base_date = ''
        if not previous.empty:
            base_date = previous['tanggal'].max()
            before = previous[previous['tanggal'] == base_date]
            for current, baseline in [('ndvi', 'ndvi_sebelumnya'), ('luas_akhir_ha', 'luas_awal_ha')]:
                if current in before and baseline not in values and before[current].notna().any():
                    values[baseline] = float(before[current].median())
        constraints = []
        for key, blocked in [('legal_status', rules['blocked_legal']), ('landcover_type', rules['excluded_landcovers'])]:
            if key in last:
                seen = {str(v).strip().lower().replace(' ', '_') for v in last[key].dropna()}
                constraints.extend(sorted(seen.intersection(blocked)))
        values['pembatas'] = ', '.join(constraints)
        values['is_demo'] = bool(last['is_demo'].any()) if 'is_demo' in last else False
        records.append(dict(values, lokasi=loc, kabupaten_kota=region, tanggal=when,
                            tanggal_pembanding=base_date, jumlah_baris=len(visits), ulangan_terakhir=len(last)))
    return records


def evidence(site):
    features, reasons = {}, []
    ndvi, prev = site.get('ndvi'), site.get('ndvi_sebelumnya')
    decline = False
    if ndvi is not None:
        features['ndvi'] = (1 - ndvi) / 2
        if prev is None:
            reasons.append(f'NDVI {fmt(ndvi)}')
        else:
            drop = prev - ndvi
            features['delta'] = float(np.clip(drop / 0.4, 0, 1))
            reasons.append(f'NDVI {fmt(prev)} → {fmt(ndvi)}')
            decline |= drop >= 0.1 - 1e-10
    if (pixels := site.get('piksel_menurun_pct')) is not None:
        features['piksel'] = pixels / 100
        reasons.append(f'{fmt(pixels, 1)}% piksel turun ≥0,10 NDVI')
        decline |= pixels >= 25
    if (canopy := site.get('tutupan_pct')) is not None:
        features['tajuk'] = 1-canopy/100
        reasons.append(f'Tutupan tajuk {fmt(canopy, 1)}%')
    loss = site.get('kehilangan_pct')
    if loss is None and site.get('luas_awal_ha', 0) > 0 and site.get('luas_akhir_ha') is not None:
        loss = max(0, 100 * (1-site['luas_akhir_ha']/site['luas_awal_ha']))
    if loss is not None:
        features['hilang'] = loss/100
        reasons.append(f'Kehilangan luas {fmt(loss, 1)}%')
        decline |= loss >= 10
    if (density := site.get('kerapatan')) is not None:
        # A continuous monotone transform, not a damage or legal threshold.
        features['pohon'] = 1 / (1 + density / 1000)
        reasons.append(f'Kerapatan {fmt(density, 0)} pohon/ha')
    return features, reasons, decline


def analyse_sheet(frame):
    sites = latest_sites(frame)
    by_features = {}
    for site in sites:
        x, reasons, decline = evidence(site)
        site.update(profil=' · '.join(INDICATORS[k] for k in x), alasan=' · '.join(reasons),
                    kelompok='—', urutan=None, indeks=None, metode='Indikator saja', status=MONITOR)
        if site['pembatas']:
            site.update(status=EXCLUDED, alasan='Pembatas pada datasheet: '+site['pembatas'],
                        metode='Aturan pembatas lahan', profil='Pembatas lahan')
        elif x:
            by_features.setdefault(tuple(x), []).append((site, list(x.values()), decline))
        else:
            site.update(status=INSUFFICIENT, alasan='Tambahkan NDVI, tutupan, kerapatan, kehilangan, atau dua luas mangrove yang sebanding.',
                        metode='Tanpa indikator', profil='Tanpa indikator')
    for rows in by_features.values():
        matrix = np.array([r[1] for r in rows])
        groups = np.zeros(len(rows), dtype=int)
        names = ['Tanpa kelompok']
        distinct = len(np.unique(matrix, axis=0))
        if len(rows) >= 3 and distinct >= 2:
            k = min(3, distinct, max(2, len(rows)//2))
            with threadpool_limits(limits=1):
                model = KMeans(n_clusters=k, n_init=10, random_state=42).fit(matrix)
            order = np.argsort(-model.cluster_centers_.mean(axis=1), kind='stable')
            groups = np.argsort(order)[model.labels_]
            names = ['Lebih tinggi', 'Lebih rendah'] if k == 2 else ['Lebih tinggi', 'Menengah', 'Lebih rendah']
        for j, (site, features, decline) in enumerate(rows):
            idx = float(np.mean(features))
            site['indeks'] = round(100*idx, 2)
            if len(names) > 1:
                site.update(kelompok=names[groups[j]], metode='K-Means')
            if decline:
                site['status'] = CANDIDATE
            elif (len(names) > 1 and groups[j] == 0) or site.get('ndvi', 1) < 0.3 or site.get('tutupan_pct', 100) < 30:
                site['status'] = VERIFY
            elif len(names) == 1 and not any(k in site for k in ('ndvi_sebelumnya', 'kehilangan_pct', 'piksel_menurun_pct')):
                site['status'] = VERIFY
        # Rank candidates first, then the learned condition group, then the pressure index.
        ordered = sorted(range(len(rows)), key=lambda j: (
            [CANDIDATE, VERIFY, MONITOR].index(rows[j][0]['status']), groups[j], -rows[j][0]['indeks'],
            rows[j][0]['kabupaten_kota'], rows[j][0]['lokasi']))
        for rank, j in enumerate(ordered, 1):
            rows[j][0]['urutan'] = rank
    result = pd.DataFrame(sites)
    result['_missing'] = result.urutan.isna()
    return result.sort_values(['_missing', 'profil', 'urutan', 'kabupaten_kota', 'lokasi'],
                              na_position='last', ignore_index=True).drop(columns='_missing')
