from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mangrove_fit.data_io import parse_upload
if len(sys.argv)!=2:
    raise SystemExit('Pemakaian: python scripts/check_data.py data.csv')
p=Path(sys.argv[1])
zones,meta=parse_upload(p.read_bytes(),p.name)
print(f'VALID: {len(zones)} zona, EPSG:4326; SHA-256 {meta["checksum"]}')
