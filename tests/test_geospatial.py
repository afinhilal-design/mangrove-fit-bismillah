import pytest
from mangrove_fit.geospatial import validate_geometry,area_ha
from mangrove_fit.schemas import ValidationError

def test_self_intersection():
    with pytest.raises(ValidationError,match='Self-intersection'):
        validate_geometry({'type':'Polygon','coordinates':[[[0,0],[1,1],[0,1],[1,0],[0,0]]]})

def test_unclosed_ring():
    with pytest.raises(ValidationError,match='tertutup'):
        validate_geometry({'type':'Polygon','coordinates':[[[0,0],[1,0],[1,1],[0,1]]]})

def test_projected_area_against_geodesic_reference(zones):
    from pyproj import Geod
    from shapely.geometry import shape
    g=zones[0]['geometry'];ref=abs(Geod(ellps='WGS84').geometry_area_perimeter(shape(g))[0])/10000
    assert abs(area_ha(g)-ref)/ref<.005 and 50<area_ha(g)<150

def test_no_area_for_point():
    assert area_ha({'type':'Point','coordinates':[112,-6]}) is None

def test_multi_utm_equal_area():
    from pyproj import Geod
    from shapely.geometry import shape
    g={'type':'Polygon','coordinates':[[[113.9,-6],[114.1,-6],[114.1,-6.1],[113.9,-6.1],[113.9,-6]]]}
    ref=abs(Geod(ellps='WGS84').geometry_area_perimeter(shape(g))[0])/10000
    assert abs(area_ha(g)-ref)/ref<.001
