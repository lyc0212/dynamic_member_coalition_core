"""One bounded read-only audit of existing originals. New output only here."""
from pathlib import Path
import sys
import json
import traceback
from fractions import Fraction
from statistics import mean
from time import perf_counter,process_time

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[1]
sys.path.insert(0,str(REPO))
from POSTHOC_AUDITOR import audit
from POSTHOC_METHOD_VALIDITY import method_validity

def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,ensure_ascii=False)

def main():
    cpu,wall=process_time(),perf_counter()
    folder=REPO/'runs/a2_prediction_sw3_test_001'
    read=lambda p:json.loads(Path(p).read_bytes())
    descriptor=read(folder/'TRUSTED_INDEX_DESCRIPTOR.json')
    evidence=read(folder/'RUN_EVIDENCE.json')
    save('NUMERIC_DIAGNOSIS.json',dict(python=sys.version,
        binary64_lambda_fraction=str(Fraction(.1)),decimal_lambda_fraction=str(Fraction('0.1')),
        exact_mathematical_total=str(Fraction(3,40)),exact_binary64_lambda_weighted_total=str(Fraction(.1)*Fraction(3,4)),
        flat_explanation=mean([.1]*24+[0.]*8),family_explanation=mean([mean([.1]*4)]*6+[mean([0.]*4)]*2),
        tolerance_used=False,explanation='Actual grouping is recomputed separately from sealed inputs; these expressions only explain the known representation.'))
    statistics=audit(folder,descriptor)
    save('POSTHOC_STATISTICAL_AUDIT.json',statistics)
    result=method_validity(folder,descriptor,mode='FORMAL_RUN',run_evidence=evidence)
    save('POSTHOC_METHOD_VALIDITY.json',result)
    save('AUDIT_TIMING.json',dict(cpu=process_time()-cpu,wall=perf_counter()-wall))
    print(json.dumps(dict(method_valid=result['METHOD_VALID'],mean_D=statistics['mean_D'],
        result=statistics['dual_numeric']['result'],secondary_checks=len(statistics['secondary_details']),
        numeric_checks=len(statistics['dual_numeric']['checks']),model=result['model_wls']['total']),indent=2))

if __name__=='__main__':
    try:main()
    except Exception as error:
        save('AUDIT_FAILURE.json',dict(error=repr(error),traceback=traceback.format_exc()))
        raise
