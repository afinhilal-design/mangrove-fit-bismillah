import math
from shapely.geometry import shape, mapping
from shapely.validation import explain_validity
from shapely.ops import transform
from pyproj import CRS, Transformer
from .schemas import ValidationError
from .config import MAX_VERTICES

def validate_geometry(geometry):
    if not isinstance(geometry,dict) or geometry.get('type') not in ('Point','Polygon','MultiPolygon'):
        raise ValidationError('INVALID_GEOMETRY: hanya Point, Polygon, atau MultiPolygon.')
    count = 0
    def walk(coords):
        nonlocal count
        if not isinstance(coords,(list,tuple)) or not coords:
            raise ValidationError('INVALID_GEOMETRY: koordinat kosong/tidak sah.')
        if isinstance(coords[0],(int,float)):
            count += 1
            if count > MAX_VERTICES: raise ValidationError('Geometri terlalu besar.')
            if len(coords) != 2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in coords):
                raise ValidationError('Koordinat wajib [longitude, latitude] 2D numerik.')
            lon,lat = coords
            if not -180 <= lon <= 180: raise ValidationError('longitude harus -180 sampai 180.')
            if not -90 <= lat <= 90: raise ValidationError('latitude harus -90 sampai 90.')
        else:
            for part in coords: walk(part)
    walk(geometry.get('coordinates'))
    polys = [geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates'] if geometry['type']=='MultiPolygon' else []
    for poly in polys:
        for ring in poly:
            if len(ring)<4 or ring[0]!=ring[-1]:
                raise ValidationError('Ring polygon minimal 4 koordinat dan harus tertutup.')
    try: g = shape(geometry)
    except Exception as e: raise ValidationError(f'INVALID_GEOMETRY: {e}') from e
    if g.is_empty or not g.is_valid:
        raise ValidationError(f'INVALID_GEOMETRY: {explain_validity(g)}')
    if g.bounds[2]-g.bounds[0] > 180:
        raise ValidationError('Polygon melintasi antimeridian belum didukung MVP.')
    return dict(mapping(g))

def area_ha(geometry):
    g = shape(geometry)
    if g.geom_type=='Point': return None
    minx,miny,maxx,maxy = g.bounds
    c = g.centroid
    z1 = min(60, max(1,int((minx+180)//6)+1))
    z2 = min(60, max(1,int((maxx+180)//6)+1))
    if z1==z2 and -80 < miny <= maxy < 84 and (miny>=0 or maxy<=0):
        target = CRS.from_epsg((32600 if c.y>=0 else 32700)+z1)
    else:
        target = CRS.from_proj4(f'+proj=laea +lat_0={c.y} +lon_0={c.x} +datum=WGS84 +units=m')
    tf = Transformer.from_crs('EPSG:4326',target,always_xy=True)
    return transform(tf.transform,g).area / 10000

def center(geometry):
    c = shape(geometry).representative_point()
    return c.y,c.x
