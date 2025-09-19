import numpy as np

def sanitize_for_json(obj):
    """Convierte np.* y otros tipos no serializables a nativos de python"""
    if isinstance(obj,dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj,list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj,tuple):
        return tuple(sanitize_for_json(v) for v in obj)
    elif isinstance(obj, (np.generic,)):
        return obj.item()
    elif hasattr(obj,"__dict__"):
        return sanitize_for_json(obj.__dict__)
    else:
        return obj