def recorded_freeze(self, tick):
    remaining = []
    for row in self.pending:
        _capture = self._record_before(row, tick)
        try:
            if row['available_tick'] > tick:
                remaining.append(row)
                continue
            j = row['target_id']
            e = row['estimate']
            b = self.states[j]
            self.consumed.append(dict(target_id=j, measurement_tick=row['measurement_tick'], available_tick=row['available_tick'], consumed_tick=tick))
            if e is None or not e.get('has_accepted_estimate') or (not e.get('optimizer_converged')) or any((e.get(k, True) for k in ('numerical_ill_conditioned', 'ambiguity_detected', 'boundary_active', 'numeric_contract_violation'))):
                continue
            p = e['estimate']
            t = row['measurement_tick']
            if len(p) != 2 or not all((math.isfinite(x) for x in p)):
                continue
            if self.history[j] and t <= self.history[j][-1][0]:
                continue
            previous = next(((s, q) for s, q in reversed(self.history[j]) if t - s >= 5), None)
            velocity = list(b['velocity_estimate'])
            if previous:
                s, q = previous
                velocity = [(x - y) / ((t - s) * DT) for x, y in zip(p, q)]
                limit = next((a['speed_limit'] for a in self.announcements if a['id'] == j))
                speed = math.hypot(*velocity)
                if speed > limit:
                    velocity = [v * limit / speed for v in velocity]
            self.history[j].append((t, list(p)))
            self.accepted_receipts[j] = self.consumed[-1].copy()
            b.update(estimate_tick=t, available_tick=row['available_tick'], position_estimate=list(p), velocity_estimate=velocity, velocity_source='ACTUAL_POSITION_DIFFERENCE' if previous else b['velocity_source'], last_observation_tick=t, source='ACTUAL_WLS', status='OBSERVED', diagnostics=deepcopy(e))
        finally:
            self._record_after(row, tick, _capture)
    self.pending = remaining
    snapshot = deepcopy(self.states)
    for b in snapshot.values():
        if b['last_observation_tick'] is not None and tick - b['last_observation_tick'] > 20:
            b['status'] = 'DEGRADED'
    return snapshot
