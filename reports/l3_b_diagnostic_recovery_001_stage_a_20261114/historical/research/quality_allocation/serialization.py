def serialize(obs):
    return {'config': obs.config.to_dict(), 'stage': obs.stage, 'time': obs.time,
            'positions': obs.positions.tolist(), 'targets': [t.to_dict() for t in obs.targets],
            'assignment': [a.to_dict() for a in obs.assignment],
            'new_ids': list(obs.new_ids), 'ended_ids': list(obs.ended_ids)}
