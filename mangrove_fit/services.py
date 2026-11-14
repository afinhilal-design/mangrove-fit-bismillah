from datetime import datetime, timezone
import copy
from .screening import run_screening
from .recommendations import recommend
from .model_service import get_model_status
from .preprocessing import completeness
from .config import WATERMARK

def analyse_zone(zone):
    screening = run_screening(zone)
    qualities = {o['quality_flag'] for o in zone['observations'].values() if o['value'] is not None}
    quality = 'DEMO' if zone['is_demo'] else 'MISSING' if not qualities else 'MEASURED' if qualities=={'measured'} else 'MIXED' if len(qualities)>1 else next(iter(qualities)).upper()
    return {'zone_id':zone['zone_id'],'analysis_timestamp':datetime.now(timezone.utc).isoformat(),'analysis_mode':'RULE_BASED','data_quality':quality,'screening':screening,'model':get_model_status(),'recommendation':recommend(zone,screening),'completeness':completeness(zone),'human_review_required':True,'warnings':([WATERMARK] if zone['is_demo'] else [])+screening['warnings'],'feature_snapshot':copy.deepcopy(zone)}
