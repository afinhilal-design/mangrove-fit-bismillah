"""Rebuild the regional snapshot using public BIG geometry and Sentinel-2 L2A COGs.

Run with the application requirements plus rasterio. The optional cache keeps fetched
scenes reusable. Publication happens after both years and both tiles have succeeded.
"""
import argparse
import csv
import hashlib
import json
import os
import math
import shutil
import tempfile
import warnings
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import from_bounds
from shapely import make_valid, union_all
from shapely.geometry import box, mapping, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
MANGROVE = 'https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/57'
DISTRICTS = 'https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3'
STAC = 'https://earth-search.aws.element84.com/v1'
COLLECTION = 'sentinel-2-c1-l2a'
TO_UTM = Transformer.from_crs(4326, 32749, always_xy=True).transform
TO_LONLAT = Transformer.from_crs(32749, 4326, always_xy=True).transform
PIXEL = 20


def request_json(url, params):
    with urlopen(url + '?' + urlencode(params), timeout=90) as response:
        doc = json.load(response)
    if 'error' in doc:
        raise RuntimeError(str(doc['error']))
    return doc


def areas(service, field, fields, tolerance=None):
    params = {'where': f"UPPER({field}) LIKE '%SIDOARJO%' OR UPPER({field}) LIKE '%SURABAYA%'",
              'outFields': fields, 'outSR': 4326, 'geometryPrecision': 6, 'f': 'geojson',
              'orderByFields': 'objectid', 'resultRecordCount': 1000}
    if tolerance:
        params['maxAllowableOffset'] = tolerance
    doc = request_json(service + '/query', params)
    features = doc['features']
    if not features or len(features) == 1000 or doc.get('exceededTransferLimit'):
        raise ValueError('Periksa jumlah fitur sumber BIG sebelum menerbitkan data.')
    return features


def grid_for_region():
    inventory = areas(MANGROVE, 'kab', 'objectid,kab,kttj,thnbuat,lsmgr')
    districts = areas(DISTRICTS, 'wadmkk', 'objectid,wadmkc,wadmkk,kdcpum', 0.000075)
    masks = {}
    for region in ('Sidoarjo', 'Kota Surabaya'):
        masks[region] = union_all([make_valid(shape(f['geometry'])) for f in inventory
                                  if f['properties']['kab'] == region])
    xmin, ymin, xmax, ymax = transform(TO_UTM, union_all(list(masks.values()))).bounds
    left = math.floor(xmin / PIXEL) * PIXEL
    top = math.ceil(ymax / PIXEL) * PIXEL
    width, height = math.ceil((xmax-left)/PIXEL), math.ceil((top-ymin)/PIXEL)
    affine = from_origin(left, top, PIXEL, PIXEL)
    roi, records, outline = [], [], []
    for feature in sorted(districts, key=lambda f: f['properties']['kdcpum']):
        p, g = feature['properties'], make_valid(shape(feature['geometry']))
        region = 'Kota Surabaya' if p['wadmkk'] == 'Kota Surabaya' else 'Sidoarjo'
        mask = g.intersection(masks[region])
        polygon = {'type': 'Feature', 'properties': {'nama': p['wadmkc'], 'wilayah': region},
                   'geometry': mapping(g.simplify(0.0006, preserve_topology=True))}
        outline.append(polygon)
        if mask.is_empty or mask.area == 0:
            continue
        projected = transform(TO_UTM, mask)
        if projected.area < PIXEL ** 2:
            continue
        point = mask.representative_point()
        records.append({'lokasi': p['wadmkc'], 'kabupaten_kota': region, 'kode_kecamatan': p['kdcpum'],
                        'longitude': round(point.x, 6), 'latitude': round(point.y, 6)})
        roi.append((mapping(projected), len(records)))
    labels = rasterize(roi, out_shape=(height, width), transform=affine, dtype='uint16')
    return records, labels, affine, outline, sorted({f['properties']['thnbuat'] for f in inventory})


def scene_list(tile, bounds, start, end):
    west, south, east, north = transform(TO_LONLAT, box(*bounds)).bounds
    footprint = box(west, south, east, north)
    params = {'collections': COLLECTION, 'bbox': ','.join(map(str, footprint.bounds)),
              'datetime': f'{start}T00:00:00Z/{end}T23:59:59Z', 'limit': 100}
    doc = request_json(STAC + '/search', params)
    features = list(doc['features'])
    while (link := next((link for link in doc['links'] if link['rel'] == 'next'), None)):
        with urlopen(link['href'], timeout=90) as response:
            doc = json.load(response)
        features.extend(doc['features'])
    selected = {}
    for item in sorted(features, key=lambda i: i['properties']['datetime'], reverse=True):
        when = item['properties']['datetime'][:10]
        if item['id'].split('_')[1].lstrip('T') != tile or when in selected:
            continue
        fraction = shape(item['geometry']).intersection(footprint).area / footprint.area
        if fraction >= 0.90 and item['properties']['eo:cloud_cover'] <= 70:
            selected[when] = item
        if len(selected) == 4:
            break
    if len(selected) < 2:
        raise ValueError(f'Terlalu sedikit citra {tile} pada {start}–{end}.')
    return list(selected.values())


@contextmanager
def open_band(asset, cache):
    # A local temporary file also works with HTTP proxies that do not support GDAL range reads.
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        path = Path(tmp) / 'band.tif'
        with urlopen(asset['href'], timeout=120) as response, path.open('wb') as local:
            shutil.copyfileobj(response, local, length=1024 * 1024)
        if path.stat().st_size != asset['file:size']:
            raise OSError('Band Sentinel-2 tidak terunduh lengkap.')
        signature = asset.get('file:checksum', '')
        if signature.startswith('1220'):
            with path.open('rb') as data:
                if hashlib.file_digest(data, 'sha256').hexdigest() != signature[4:]:
                    raise OSError('Checksum band Sentinel-2 tidak cocok.')
        with rasterio.open(path) as dataset:
            yield dataset


def read_scene(item, bounds, size, cache):
    key = hashlib.sha256(repr((bounds, size, PIXEL, 'v1')).encode()).hexdigest()[:12]
    dest = cache / (item['id'] + '-' + key + '.npz')
    if dest.exists():
        with np.load(dest) as saved:
            return saved['v']
    bands = {}
    for key in ('scl', 'red', 'nir'):
        asset = item['assets'][key]
        with open_band(asset, cache) as ds:
            if ds.crs.to_epsg() != 32749:
                raise ValueError('CRS citra berubah.')
            window = from_bounds(*bounds, transform=ds.transform)
            array = ds.read(1, window=window, out_shape=size, masked=True,
                            resampling=rasterio.enums.Resampling.nearest)
        meta = asset['raster:bands'][0]
        bands[key] = (array.astype('float32') * meta.get('scale', 1) + meta.get('offset', 0)).filled(np.nan)
    red, nir = bands['red'], bands['nir']
    valid = np.isin(bands['scl'], [4, 5, 6]) & (red >= 0) & (nir >= 0) & ((red+nir) > 0)
    ndvi = np.full(size, np.nan, dtype='float32')
    np.divide(nir-red, nir+red, out=ndvi, where=valid)
    np.savez_compressed(dest, v=ndvi)
    print(item['id'], 'valid pixels', np.isfinite(ndvi).sum(), flush=True)
    return ndvi


def season(tile, bounds, size, start, end, cache):
    scenes = scene_list(tile, bounds, start, end)
    print(tile, start, [i['id'] for i in scenes], flush=True)
    stack = np.stack([read_scene(s, bounds, size, cache) for s in scenes])
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        median = np.nanmedian(stack, axis=0)
    median[np.isfinite(stack).sum(axis=0) < 2] = np.nan
    return median, [i['id'] for i in scenes]


def build(end, cache, dest):
    records, labels, affine, outline, mask_years = grid_for_region()
    prev = end.replace(year=end.year-1, day=28 if (end.month, end.day) == (2, 29) else end.day)
    periods = [(d - timedelta(days=39), d) for d in (prev, end)]
    height, width = labels.shape
    split = int((affine.f - 9200000) / PIXEL)
    parts = [('49MFN', 0, split), ('49MFM', split, height)]
    composites = [np.full(labels.shape, np.nan, dtype='float32') for _ in periods]
    sources = {}
    cache.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = []
        for tile, r0, r1 in parts:
            bounds = (affine.c, affine.f-r1*PIXEL, affine.c+width*PIXEL, affine.f-r0*PIXEL)
            for yr, (start, stop) in enumerate(periods):
                jobs.append((pool.submit(season, tile, bounds, (r1-r0, width), start, stop, cache), tile, r0, r1, yr))
        for job, tile, r0, r1, yr in jobs:
            values, scene_ids = job.result()
            composites[yr][r0:r1] = values
            sources[f'{periods[yr][1].year}_{tile}'] = scene_ids
    matched = np.isfinite(composites[0]) & np.isfinite(composites[1])
    for i, row in enumerate(records, 1):
        loc = labels == i
        keep = matched & loc
        n, total = int(keep.sum()), int(loc.sum())
        row.update({'piksel_acuan': total, 'piksel_valid': n, 'cakupan_valid_pct': round(100*n/total, 1) if total else 0,
                    'awal_pembanding': periods[0][0], 'akhir_pembanding': prev,
                    'awal_pengamatan': periods[1][0], 'akhir_pengamatan': end,
                    'ndvi_sebelumnya': None, 'ndvi': None, 'piksel_menurun_pct': None})
        if n >= 20 and n >= total * 0.5:
            older, newer = [a[keep] for a in composites]
            row.update(ndvi_sebelumnya=round(float(np.median(older)), 4), ndvi=round(float(np.median(newer)), 4),
                       piksel_menurun_pct=round(float(100*np.mean((newer-older) <= -0.10)), 1))
    if not all(any(r['ndvi'] is not None and r['kabupaten_kota'] == k for r in records)
               for k in ('Sidoarjo', 'Kota Surabaya')):
        raise RuntimeError('Cakupan tidak cukup untuk kedua wilayah.')
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {'cutoff': end.isoformat(), 'periods': [[str(x) for x in pair] for pair in periods],
                'mask_years': mask_years, 'mask_url': MANGROVE, 'admin_url': DISTRICTS, 'stac': STAC, 'collection': COLLECTION,
                'scenes': sources, 'minimum_pixels': 20, 'minimum_coverage': 0.5, 'resolution_m': PIXEL}
    with tempfile.TemporaryDirectory(dir=dest) as temp:
        stage = Path(temp) / 'snapshot'
        stage.mkdir()
        with (stage / 'lokasi.csv').open('w', newline='', encoding='utf-8') as f:
            out = csv.DictWriter(f, fieldnames=list(records[0]))
            out.writeheader()
            out.writerows(records)
        (stage / 'kecamatan.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': outline}, separators=(',', ':')), encoding='utf-8')
        (stage / 'sumber.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
        import_sources(stage, dest, end)
    print('Published', len(records), 'districts', flush=True)


def import_sources(stage, dest, end):
    # Readers follow one atomic pointer. Older readers can finish on the previous edition.
    digest = hashlib.sha256()
    for name in ('lokasi.csv', 'kecamatan.geojson', 'sumber.json'):
        digest.update((stage/name).read_bytes())
    version = str(end)+'-'+digest.hexdigest()[:12]
    published = dest/version
    try:
        stage.rename(published)
    except OSError:
        if not published.is_dir() or any((stage/f).read_bytes() != (published/f).read_bytes()
                                          for f in ('lokasi.csv', 'kecamatan.geojson', 'sumber.json')):
            raise
    with tempfile.NamedTemporaryFile(dir=dest, mode='w', encoding='ascii', delete=False) as handle:
        handle.write(version+'\n')
        pointer = Path(handle.name)
    os.replace(pointer, dest/'aktif.txt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tanggal', type=date.fromisoformat, required=True, help='Tanggal akhir yang sudah berlalu, YYYY-MM-DD')
    parser.add_argument('--cache', type=Path, default=Path(tempfile.gettempdir())/'mangrove-fit-s2')
    parser.add_argument('--output', type=Path, default=ROOT/'data'/'pesisir')
    args = parser.parse_args()
    build(args.tanggal, args.cache, args.output)
