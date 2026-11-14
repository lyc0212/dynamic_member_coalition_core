"""Static observations only. Does not step an environment or run an episode."""
from fractions import Fraction
from pursuit_v2.service_m3 import make_service_m3_policy,POLICY_NAME
from .fixtures import frozen_cases
from .worlds import public_request
from .model import candidates
from .reference import evaluate,mean_score
from .additive import enumerate_optimum,table_value


def audit_interface():
    output=[]
    for fixture in frozen_cases():
        obs=fixture.obs
        request=public_request(obs,fixture.until)
        before=request.identity
        specs=candidates(request)
        values=[mean_score(evaluate(request,s)) for s in specs]
        _,optimum,plans=enumerate_optimum(request,specs,values)
        policy=make_service_m3_policy(POLICY_NAME,until=fixture.until)
        first=policy.decide(obs); second=policy.decide(obs)
        assert first.assignment==second.assignment and first.log==second.log
        assert public_request(obs,fixture.until).identity==before
        cert=first.log['certificate']
        assert Fraction(cert['L'])==Fraction(cert['U'])==optimum
        keys=tuple((row['target'],tuple(row['robots']),tuple(row['roles'])) for row in first.log['selected'])
        assert keys in [k for k,_ in plans]
        assert table_value(request,keys,{s.key:v for s,v in zip(specs,values)})==optimum
        from .additive import assignment
        assert first.assignment==assignment(request,keys)
        output.append(dict(case=fixture.name,public_request=request.payload(),request_identity=before,
                           independent_optimum=str(optimum),assignment=[a.to_dict() for a in first.assignment],
                           decision=first.log,repeat_identical=True,input_unchanged=True))
    return output
