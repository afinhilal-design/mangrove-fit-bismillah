from .config import load_rules

def completeness(zone):
    core = load_rules()['core_parameters']
    available = sum(zone['observations'].get(k,{}).get('value') is not None for k in core)
    return {'available':available,'total':len(core),'percent':round(100*available/len(core))}
