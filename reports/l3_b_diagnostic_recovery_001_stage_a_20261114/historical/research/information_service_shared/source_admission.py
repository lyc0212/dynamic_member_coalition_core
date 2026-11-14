"""Exact external source bindings. Hashes in caller-owned objects grant no trust."""
from copy import deepcopy
from pathlib import Path
import time
from .common import ContractError, digest, read_json, sha_file

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'docs/STAGE2A5B_GQ_SHARED_FULL_PROTOCOL_LOCK.json'
LOCK_SHA = 'e2b0ecc0beb971fd8e90235c13c4b843c8c45a5a82da5e88e07b661ba920fda8'


def check_pin(pin, *, root=ROOT, historical_census_link=False):
    path = Path(pin['path'])
    if not path.is_absolute():
        path = Path(root) / path
    if (path.is_symlink() and not historical_census_link) or not path.is_file():
        raise ContractError('Expected existing regular pinned file: ' + str(path))
    data = path.read_bytes()
    import hashlib
    if hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ContractError('External file pin mismatch: ' + str(path))
    size = pin.get('size_bytes', pin.get('size'))
    if size is not None and len(data) != size:
        raise ContractError('External file size mismatch: ' + str(path))
    return path.resolve()


def source_census():
    """Trusted launcher metadata work, never run in the scientific predictor."""
    start, cpu = time.monotonic(), time.process_time()
    if sha_file(LOCK) != LOCK_SHA:
        raise ContractError('Wrong shared preparation revision')
    lock = read_json(LOCK)
    receipts = []
    for name, row in lock['files'].items():
        check_pin(dict(path=name, **row))
    for item in lock['source_protection']:
        path = check_pin(item['manifest'])
        manifest = read_json(path)['files']
        if len(manifest) != item['count']:
            raise ContractError('Protected source census count changed')
        rows = []
        for name, sha in sorted(manifest.items()):
            # Old protection manifests intentionally contain denial-probe
            # symlinks. Inspect their frozen target bytes as provenance only;
            # this exception never grants a worker data-input permission.
            p = check_pin(dict(path=name, sha256=sha), historical_census_link=True)
            named=ROOT/name
            rows.append(dict(path=name, sha256=sha, size_bytes=p.stat().st_size,
                historical_probe_symlink=named.is_symlink(),
                symlink_target=str(named.readlink()) if named.is_symlink() else None))
        receipts.append(dict(manifest=item['manifest'], count=len(rows), files=rows))
    seal_path = check_pin(lock['source_seal'])
    assets = []
    for name, pin in read_json(seal_path)['files'].items():
        p = check_pin(dict(path=name, **pin), root=seal_path.parent)
        assets.append(dict(path=str(p.relative_to(ROOT)), sha256=pin['sha256'], size_bytes=p.stat().st_size))
    if len(assets) != 84:
        raise ContractError('r2 seal asset membership changed')
    registry_path = check_pin(lock['source_registry'])
    registry = read_json(registry_path)
    if len(registry) != 35:
        raise ContractError('r2 actual registry membership changed')
    artifact_rows = []
    for row in registry:
        for key, pin in row['artifacts'].items():
            path = check_pin(pin)
            artifact_rows.append(dict(episode=row['episode_id'], tick=row['tick'], artifact=key,
                                      path=str(path), sha256=pin['sha256']))
    return dict(passed=True, preparation_lock_sha256=LOCK_SHA, source_manifests=receipts,
                original_assets=assets, actual_registry_pin=lock['source_registry'],
                actual_registry_entries=35, actual_artifacts=artifact_rows,
                trusted_launcher_cpu=time.process_time()-cpu, wall=time.monotonic()-start,
                scientific_calls=0, source_scope='PROJECT_LOCAL_ONLY')


def validate_census_receipt(receipt, expected):
    # expected is separately pinned by the launcher, never extracted from receipt.
    if type(receipt) is not dict or receipt.get('passed') is not True:
        raise ContractError('Unsuccessful source census')
    if digest(receipt) != expected:
        raise ContractError('Census receipt differs from external binding')
    for m in receipt['source_manifests']:
        paths = [r['path'] for r in m['files']]
        if len(paths) != m['count'] or len(set(paths)) != len(paths):
            raise ContractError('Missing or duplicate census member')
    if [m['count'] for m in receipt['source_manifests']] != [267,227,139,122]:
        raise ContractError('Wrong source membership counts')
    return dict(passed=True)


def admit_original(snapshot, registry, registry_sha, *, registry_path):
    """Auditor validates actual registered origin before predictors get public data."""
    if sha_file(registry_path) != registry_sha:
        raise ContractError('Original registry external pin changed')
    key = (snapshot['episode'], snapshot['tick'])
    rows = [r for r in registry if (r['episode_id'], r['tick']) == key]
    if len(rows) != 1:
        raise ContractError('Original source not uniquely registered')
    row = rows[0]
    result_pin = snapshot['source_registration']['registered_execution_result_auditor_only']
    result = read_json(check_pin(result_pin))
    if Path(row['registered_execution_result']).resolve() != check_pin(result_pin):
        raise ContractError('Foreign execution producer')
    if result.get('passed') is not True or result['checkpoint_id'] != row['checkpoint_id']:
        raise ContractError('Actual source did not commit')
    clean = {}
    for name, pin in snapshot['public_inputs'].items():
        path = check_pin(pin)
        recorded = row['artifacts'][name]
        if path != Path(recorded['path']).resolve() or recorded['sha256'] != pin['sha256']:
            raise ContractError('Unregistered public source path or identity')
        clean[name] = read_json(path)
    from research.information_service_online import public
    auth = public.HistoryAuthority.from_public_binding(clean['public_binding'])
    req = public.validate_request(clean['evaluation_request'], auth)
    if req['checkpoint'] != clean['public_checkpoint'] or req['checkpoint']['checkpoint_id'] != row['checkpoint_id']:
        raise ContractError('Checkpoint and actual binding disagree')
    expected = public.build_manifest(req, auth)['candidates']
    if [r['candidate'] for r in clean['candidate_catalog']] != expected:
        raise ContractError('Public candidate catalog differs from canonical enumeration')
    return dict(passed=True, source_kind='R2_ACTUAL_REGISTERED', episode=key[0],tick=key[1],
                checkpoint_id=row['checkpoint_id'], request_identity=req['evaluation_request_id'],
                public_inputs=deepcopy(snapshot['public_inputs']))


def validate_new_receipt(receipt, *, attempt_id, episode_id, previous=None, unit_only=False):
    """Pure receipt contract also used by SG03; UNIT_ONLY never grants authority."""
    if receipt.get('source_kind') != ('UNIT_ONLY' if unit_only else 'NEW_COMMITTED_EXECUTION'):
        raise ContractError('Synthetic or predicted history cannot become actual history')
    physical = ('unit:D:' if unit_only else attempt_id + ':D:') + episode_id
    if receipt.get('physical_environment_id') != physical or receipt.get('producer_role') != 'execution':
        raise ContractError('Foreign physical producer')
    if receipt.get('committed') is not True or receipt.get('producer_passed') is not True:
        raise ContractError('Uncommitted producer cannot grant a public binding')
    if receipt.get('selector_input_origin') != 'NEW_CURRENT_COMPLETE_TABLE':
        raise ContractError('Old winner cannot authorize a new action')
    if previous is None:
        if receipt['tick'] != 0 or receipt['previous_checkpoint_id'] is not None:
            raise ContractError('Fresh D starts only at tick zero')
    else:
        if (receipt['tick'] != previous['tick'] + 20 or
                receipt['previous_checkpoint_id'] != previous['checkpoint_id'] or
                receipt.get('previous_receipt_id') != digest(previous) or
                not receipt.get('successful_action_cache_link')):
            raise ContractError('Broken serial restore/action chain')
    if not receipt.get('artifacts') or not receipt.get('producer_result_pin'):
        raise ContractError('Missing actual artifact/producer binding')
    return dict(passed=True, unit_only=unit_only, grants_main_authority=not unit_only)
