from .config import load_rules

def survey_sort(results):
    order = load_rules()['survey_order']
    return sorted(results,key=lambda r:(order.index(r['screening']['status']),r['completeness']['percent'],r['zone_id']))
