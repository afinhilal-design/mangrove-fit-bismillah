import csv
import io
import json
import hashlib
from pathlib import Path
from .schemas import normalize_zone, ValidationError
from .config import MAX_UPLOAD_BYTES, MAX_FEATURES

def _json(text):
    try:
        return json.loads(text,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f'Nilai {x} tidak sah')))
    except (ValueError,TypeError,RecursionError) as e:
        raise ValidationError(f'JSON tidak sah: {e}') from e

def parse_upload(raw, filename):
    if len(raw)>MAX_UPLOAD_BYTES: raise ValidationError('Berkas melampaui batas ukuran unggahan.')
    try: text=raw.decode('utf-8-sig')
    except UnicodeDecodeError: raise ValidationError('Berkas harus berupa teks UTF-8, bukan file biner.')
    suffix=Path(filename).suffix.lower()
    rows=[]
    if suffix=='.csv':
        try:
            reader=csv.DictReader(io.StringIO(text))
            fields=reader.fieldnames or []
            if len(fields)!=len(set(fields)): raise ValidationError('Nama kolom CSV duplikat.')
            if not {'zone_id','zone_name'}.issubset(fields): raise ValidationError('CSV wajib memiliki zone_id dan zone_name.')
            if not ({'longitude','latitude'}.issubset(fields) or 'geometry' in fields): raise ValidationError('CSV perlu longitude, latitude atau kolom geometry GeoJSON.')
            for i,p in enumerate(reader,2):
                if len(rows)>=MAX_FEATURES: raise ValidationError('Jumlah zona melampaui batas.')
                if None in p: raise ValidationError(f'Baris {i}: jumlah kolom tidak sesuai header.')
                if p.get('geometry'):
                    geometry=_json(p['geometry'])
                else:
                    try: geometry={'type':'Point','coordinates':[float(p['longitude']),float(p['latitude'])]}
                    except (ValueError,TypeError,KeyError): raise ValidationError(f'Baris {i}: longitude/latitude harus angka.')
                try: rows.append(normalize_zone(p,geometry))
                except ValidationError as e: raise ValidationError(f'Baris {i}: {e}') from e
        except csv.Error as e: raise ValidationError(f'CSV tidak sah: {e}') from e
    elif suffix in ('.geojson','.json'):
        doc=_json(text)
        if not isinstance(doc,dict) or doc.get('type')!='FeatureCollection' or not isinstance(doc.get('features'),list): raise ValidationError('GeoJSON harus FeatureCollection dengan array features.')
        if doc.get('crs'):
            if not isinstance(doc['crs'],dict): raise ValidationError('CRS tidak sah.')
            name=doc['crs'].get('properties',{}).get('name','')
            if name not in ('EPSG:4326','urn:ogc:def:crs:OGC:1.3:CRS84','urn:ogc:def:crs:EPSG::4326'):
                raise ValidationError('CRS harus EPSG:4326; reproyeksikan berkas sebelum impor.')
        if len(doc['features'])>MAX_FEATURES: raise ValidationError('Jumlah fitur melampaui batas.')
        for i,f in enumerate(doc['features'],1):
            if not isinstance(f,dict) or f.get('type')!='Feature': raise ValidationError(f'Fitur {i} tidak sah.')
            try: rows.append(normalize_zone(f.get('properties'),f.get('geometry')))
            except ValidationError as e: raise ValidationError(f'Fitur {i}: {e}') from e
    else: raise ValidationError('Format tidak didukung; pilih CSV atau GeoJSON.')
    if not rows: raise ValidationError('Berkas tidak memuat zona.')
    ids=[r['zone_id'] for r in rows]
    if len(ids)!=len(set(ids)): raise ValidationError('zone_id duplikat dalam berkas.')
    return rows,{'name':Path(filename).name,'checksum':hashlib.sha256(raw).hexdigest(),'count':len(rows),'crs':'EPSG:4326','source_type':suffix,'provenance':[z['provenance'] for z in rows]}
