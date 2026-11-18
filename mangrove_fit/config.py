from pathlib import Path
import os
import hashlib
from functools import lru_cache
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
MODEL_DIR = ROOT / 'models' / 'active'
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_MB', '10')) * 1024 * 1024
MAX_FEATURES = int(os.getenv('MAX_FEATURES', '1000'))
MAX_VERTICES = 50000
WATERMARK = 'SIMULASI — BUKAN DATA LAPANGAN'
STATUS_LABELS = {'ELIGIBLE': 'Bisa dikaji lanjut', 'NEEDS_REVIEW': 'Perlu verifikasi', 'EXCLUDED': 'Tidak memenuhi screening'}
COLORS = {'ELIGIBLE': '#278267', 'NEEDS_REVIEW': '#d59b27', 'EXCLUDED': '#c55a4f', 'UNANALYSED': '#89928e'}

@lru_cache(maxsize=4)
def _parse_rules(mtime_ns, size):
    raw = (ROOT / 'config/rules.yaml').read_bytes()
    rules = yaml.safe_load(raw)
    rules['checksum'] = hashlib.sha256(raw).hexdigest()
    return rules

def load_rules():
    """Aturan di-cache per (mtime, ukuran) berkas; mengedit rules.yaml tetap langsung berlaku.

    Hasil bersifat baca-saja: jangan memodifikasi dict yang dikembalikan.
    """
    st = (ROOT / 'config/rules.yaml').stat()
    return _parse_rules(st.st_mtime_ns, st.st_size)
