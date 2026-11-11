"""Fixed archived A2_R byte binding. Not a real-source authenticator.

The manifest pin was checked against the task's fixed Git baseline before this
module was authored. Expected hashes come from that pre-existing manifest,
never from a submitted reconstructed state. No files are written.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

BASE_COMMIT = '275c26ec1bb4f848936148ccec7591115bbf68cc'
MANIFEST = 'reports/stfbs_lite_d1a_001/BASELINE.json'
MANIFEST_SHA256 = 'cf20d14365b69b24ae68579880078d46814a2024181c85cdecb80bcddfab66a0'
SEED = 'reports/stfbs_lite_d1a_001/BELIEF_REPLAY_SEED.json'
SEED_SHA256 = 'def953424b65265db7d3ede78259e278e5e36cf062c50fbf1c880690ef454b6b'
DIRECTORY = 'runs/a2_switch_episode_001/'
ARCHIVES = tuple(DIRECTORY+n for n in ('PUBLIC_INPUT.json', 'WORLD_INPUT.json', 'R.json',
    'R_D0.json', 'R_D20.json', 'R_D40.json', 'R_D60.json', 'R_D80.json', 'R_D100.json'))
PRODUCTION = ('scripts/run_a2.py', 'scripts/run_a1.py', 'research/non_oracle/belief.py',
              'research/non_oracle/environment.py', 'research/information_service_online/execution.py',
              'research/information_service_online/public.py')
_SEAL = object()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class ArchiveBindingError(ValueError):
    """Public fixed reason code, with no private data in error messages."""


@dataclass(frozen=True)
class BoundActualArchive:
    _documents_json: str
    _references_json: str
    _seed_json: str
    _seal: object

    def documents(self):
        return json.loads(self._documents_json)

    def references(self):
        return json.loads(self._references_json)

    def d60_reference_seed(self):
        return json.loads(self._seed_json)


def bind_actual_archive(repository):
    """Read fixed paths only, check legacy expectations and detach all bytes.

    The baseline pin is a versioned archival anchor, not proof that the original
    physical producer was authenticated by an independent real trust provider.
    """
    root = Path(repository).resolve()
    try:
        manifest_bytes = (root/MANIFEST).read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
            raise ArchiveBindingError('REGISTERED_MANIFEST_IDENTITY_MISMATCH')
        expected = json.loads(manifest_bytes)['tracked_fingerprints']
        documents, refs = {}, []
        for path in ARCHIVES+PRODUCTION:
            wanted = expected.get(path)
            if not isinstance(wanted, str) or len(wanted) != 64:
                raise ArchiveBindingError('INDEPENDENT_EXPECTATION_UNAVAILABLE')
            raw = (root/path).read_bytes()
            if hashlib.sha256(raw).hexdigest() != wanted:
                raise ArchiveBindingError('REGISTERED_FILE_IDENTITY_MISMATCH')
            refs.append(dict(path=path, sha256=wanted, role='ACTUAL_ARCHIVE' if path in ARCHIVES else 'PRODUCTION_RULE'))
            if path in ARCHIVES:
                documents[Path(path).name] = json.loads(raw)
        raw = (root/SEED).read_bytes()
        if hashlib.sha256(raw).hexdigest() != SEED_SHA256:
            raise ArchiveBindingError('D60_REFERENCE_SEED_IDENTITY_MISMATCH')
        refs.extend((dict(path=MANIFEST, sha256=MANIFEST_SHA256, role='INDEPENDENT_ARCHIVE_MANIFEST'),
                     dict(path=SEED, sha256=SEED_SHA256, role='REFERENCE_ONLY_NOT_REPLAY_INPUT')))
        references = dict(status='ARCHIVE_BYTES_BOUND', baseline_commit=BASE_COMMIT,
                          manifest=MANIFEST, files=refs, document_digests={k: _digest(v) for k, v in documents.items()},
                          real_source_authentication='NOT_VERIFIED')
        return BoundActualArchive(json.dumps(documents, sort_keys=True, allow_nan=False),
                                  json.dumps(references, sort_keys=True), raw.decode('utf-8-sig'), _SEAL)
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ArchiveBindingError('ARCHIVE_SOURCE_UNAVAILABLE') from None


def checked_documents(bound):
    if type(bound) is not BoundActualArchive or bound._seal is not _SEAL:
        raise ArchiveBindingError('BOUND_ACTUAL_ARCHIVE_REQUIRED')
    docs, refs = bound.documents(), bound.references()
    if (refs['baseline_commit'] != BASE_COMMIT or set(docs) != {Path(p).name for p in ARCHIVES}
            or any(_digest(v) != refs['document_digests'][k] for k, v in docs.items())):
        raise ArchiveBindingError('BOUND_DOCUMENT_IDENTITY_MISMATCH')
    return docs
