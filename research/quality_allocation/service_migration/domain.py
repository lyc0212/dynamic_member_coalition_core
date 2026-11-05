"""The migration gate is certified only for its original legacy domain."""
def require_legacy(case):
    cfg = case.obs.config
    if (cfg.geometry_mode != 'legacy_anchor' or cfg.capture_mode != 'stepwise_service'
            or any(t.required_robots not in (1, 2) for t in case.obs.targets)):
        raise ValueError('Migration gate not adapted to new observation geometry')
