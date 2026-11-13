"""Public deterministic JSON utilities; importing this module runs no science."""
import hashlib
import json
import math
import os
from pathlib import Path
from research.information_service_bridge.common import AccessDenied

CONTRACT_ID='STAGE2A5B-GQ-ONLINE-v1.0'
DT=.05
class ContractError(ValueError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
        separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()

def save_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.pending')
    with temp.open('w',encoding='utf-8') as out:
        json.dump(value,out,ensure_ascii=False,indent=2,allow_nan=False)
        out.flush();os.fsync(out.fileno())
    temp.replace(path)

def read_json(path):
    return json.loads(Path(path).read_text())

def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_label(value):
    return ''.join(c if c.isalnum() or c in '-_.' else '_' for c in str(value))

def absolute_O(components):
    return float((((components['completion']+components['flow'])+components['late'])+
                  components['effort'])+components['terminal'])

def json_safe(value):
    if isinstance(value,dict):return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_safe(v) for v in value]
    if hasattr(value,'tolist'):return json_safe(value.tolist())
    if isinstance(value,float) and not math.isfinite(value):return {'nonfinite':repr(value)}
    return value
