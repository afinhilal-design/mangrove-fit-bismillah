from pathlib import Path
import os
import hashlib
import yaml

ROOT = Path(__file__).resolve().parent.parent
# .env lokal, tanpa evaluasi kode atau ekspansi shell.
if (ROOT / '.env').exists():
    for line in (ROOT / '.env').read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///data/app.db')
DB_PATH = Path(DB_URL.removeprefix('sqlite:///'))
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_MB', '10')) * 1024 * 1024
MAX_FEATURES = int(os.getenv('MAX_FEATURES', '1000'))
MAX_VERTICES = 50000
WATERMARK = 'SIMULASI — BUKAN DATA LAPANGAN'
STATUS_LABELS = {'ELIGIBLE': 'Bisa dikaji lanjut', 'NEEDS_REVIEW': 'Perlu verifikasi', 'EXCLUDED': 'Tidak memenuhi screening'}
COLORS = {'ELIGIBLE': '#278267', 'NEEDS_REVIEW': '#d59b27', 'EXCLUDED': '#c55a4f', 'UNANALYSED': '#89928e'}

def load_rules():
    raw = (ROOT / 'config/rules.yaml').read_bytes()
    rules = yaml.safe_load(raw)
    rules['checksum'] = hashlib.sha256(raw).hexdigest()
    return rules
