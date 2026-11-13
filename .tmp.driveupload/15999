"""Preserve audit attempt 1 and correct only JSON manifest equality for attempt 2."""
from pathlib import Path
p=Path('reports/stfbs_lite_d1a_h1_revalidation_001/read_only_review.py')
s=p.read_text(encoding='utf-8')
s=s.replace("assert registration==read(OUT/'EXTERNAL_REGISTRATION.json')==precheck['source_registration']","assert digest(registration)==digest(read(OUT/'EXTERNAL_REGISTRATION.json'))==digest(precheck['source_registration'])")
s=s.replace("with (OUT/name).open('x',encoding='utf-8') as f:","with (OUT/(Path(name).stem+'_002'+Path(name).suffix)).open('x',encoding='utf-8') as f:")
with p.with_name('read_only_review_002.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
