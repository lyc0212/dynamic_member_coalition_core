"""Public-only, deterministic v1 forecast contract (no private trajectory access)."""
from pursuit_v2.service import tick, DT
from .domain import validate_observation
from .model import Case


def public_request(obs, until=None):
    validate_observation(obs)
    end=min(obs.config.end_time,obs.time+obs.config.prediction_stages*obs.config.stage_dt) if until is None else until
    end=tick(end)*DT
    # Public Targets have no future turns; this is one equal-probability CV world,
    # not a calibrated maneuver distribution or a claim about actual future.
    return Case('public_cv_v1',obs,end,(tuple(obs.targets),),expectation='interface')
