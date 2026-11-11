"""Protected local consume index. No deletion, refund or automatic recovery."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path

from research.non_oracle.stfbs_lite_real_d60_source import _require, content_digest
from research.non_oracle.stfbs_lite_real_d60_windows_boundary import inspect_protected_store


@contextmanager
def exclusive_store_lock(directory):
    import msvcrt
    path = Path(directory) / 'consumer.lock'
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if os.fstat(fd).st_size == 0:
            os.write(fd, b'1')
            os.fsync(fd)
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd)


def inspect_consume_index(directory):
    """Any orphan, removed marker or truncated index poisons the store."""
    directory = Path(directory)
    index = directory / 'consumed.jsonl'
    records, previous, attempts = [], None, set()
    if index.exists():
        raw = index.read_bytes()
        _require(raw and raw.endswith(b'\n'), 'CONSUMPTION_INDEX_TRUNCATED')
        for number, line in enumerate(raw.splitlines(), 1):
            row = json.loads(line)
            digest = row.pop('digest')
            _require(row['sequence'] == number and row['previous'] == previous
                     and content_digest(row) == digest, 'CONSUMPTION_INDEX_CORRUPT')
            _require(row['attempt_id'] not in attempts, 'CONSUMPTION_INDEX_DUPLICATE')
            marker = directory / (hashlib.sha256(row['attempt_id'].encode()).hexdigest() + '.consumed')
            _require(marker.is_file() and hashlib.sha256(marker.read_bytes()).hexdigest() == row['marker_sha256'],
                     'CONSUMED_MARKER_DELETED_OR_CHANGED')
            payload = json.loads(marker.read_bytes())
            _require(payload['attempt_id'] == row['attempt_id'] and payload['permit_digest'] == row['permit_digest']
                     and payload['status'] == 'CONSUMED_NO_REFUND', 'CONSUMPTION_IDENTITY_CONFLICT')
            attempts.add(row['attempt_id'])
            previous = digest
            records.append(dict(row, digest=digest))
    _require(len(list(directory.glob('*.consumed'))) == len(records), 'ORPHAN_CONSUMPTION_MARKER')
    return records


def protected_consume(verified, authority, *, worker_token=None):
    from research.non_oracle.stfbs_lite_real_d60_run_gates import consume_attempt
    directory, context = authority.consumption_directory, authority.execution_context
    inspect_protected_store(directory, context, worker_token=worker_token)
    with exclusive_store_lock(directory):
        inspect_protected_store(directory, context, worker_token=worker_token)
        rows = inspect_consume_index(directory)
        marker = consume_attempt(verified, directory)  # Existing O_EXCL/fsync.
        row = dict(sequence=len(rows)+1, previous=rows[-1]['digest'] if rows else None,
                   attempt_id=verified['record']['attempt_id'], permit_digest=verified['signed_envelope_digest'],
                   marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest(),
                   state='CONSUMED_NO_REFUND', marker_fsync_completed=True)
        row['digest'] = content_digest(row)
        with (Path(directory)/'consumed.jsonl').open('ab') as stream:
            payload = (json.dumps(row, sort_keys=True, separators=(',', ':'))+'\n').encode()
            _require(stream.write(payload) == len(payload), 'CONSUMPTION_INDEX_SHORT_WRITE')
            stream.flush()
            os.fsync(stream.fileno())
        inspect_protected_store(directory, context, worker_token=worker_token)
        inspect_consume_index(directory)
    return dict(marker=str(marker), index_digest=row['digest'], irreversible=True,
                durability='FILE_FSYNC_COMPLETED_WINDOWS_POWER_LOSS_NOT_VALIDATED')
