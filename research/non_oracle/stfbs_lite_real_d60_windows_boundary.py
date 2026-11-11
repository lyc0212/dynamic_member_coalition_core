"""Windows boundary checks/copy preparation. Never changes accounts or ACLs.

Checks are intentionally strict. They are not a restricted-process creator or a
Python/DLL dependency-closure proof; production isolation remains unavailable.
"""
import hashlib
import os
from pathlib import Path
import shutil

from research.non_oracle.stfbs_lite_real_d60_source import AdmissionRejected, _require

SYSTEM_SID = 'S-1-5-18'
READ_EXECUTE = 0x1200A9


def validate_acl(owner, protected, aces, *, consumer_sid, worker_sid, source):
    """Accept only explicit conventional allow ACEs for named principals.

    Reject broad groups, inherited/object/conditional ACEs and unknown rights.
    Consume store permits no worker ACE (including DELETE_CHILD/DELETE access).
    This conservative allowlist avoids treating Get-Acl summaries as effective
    access proofs. Restricted-token/group checks are separate and mandatory.
    """
    _require(consumer_sid != worker_sid and owner in {consumer_sid, SYSTEM_SID}
             and protected and bool(aces), 'UNPROTECTED_WINDOWS_OWNER_OR_DACL')
    readers, writers = set(), set()
    for ace_type, flags, mask, sid in aces:
        _require(ace_type == 0 and flags == 0 and type(mask) is int,
                 'UNSUPPORTED_OR_INHERITED_WINDOWS_ACE')
        if sid in {consumer_sid, SYSTEM_SID}:
            writers.add(sid)
        else:
            _require(source and sid == worker_sid and mask & ~READ_EXECUTE == 0,
                     'UNAUTHORIZED_WINDOWS_WRITE_OR_DELETE_RIGHTS')
            readers.add(sid)
    _require(consumer_sid in writers, 'CONSUMER_ACL_MISSING')
    if source:
        _require(worker_sid in readers, 'WORKER_READ_EXECUTE_ACL_MISSING')
    return 'EXPLICIT_WINDOWS_DACL_CONTRACT_MATCH'


def reject_reparse_chain(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        stat = item.lstat()
        _require(not getattr(stat, 'st_file_attributes', 0) & 0x400,
                 'WINDOWS_REPARSE_POINT_REJECTED')
    return path


def inspect_acl(path, *, consumer_sid, worker_sid, source):
    _require(os.name == 'nt', 'WINDOWS_REQUIRED')
    import win32security as security
    path = reject_reparse_chain(path)
    sd = security.GetNamedSecurityInfo(str(path), security.SE_FILE_OBJECT,
          security.OWNER_SECURITY_INFORMATION | security.DACL_SECURITY_INFORMATION)
    acl = sd.GetSecurityDescriptorDacl()
    _require(acl is not None, 'NULL_DACL_REJECTED')
    aces = []
    for i in range(acl.GetAceCount()):
        ace = acl.GetAce(i)
        _require(len(ace) == 3, 'NONSTANDARD_ACE_REJECTED')
        aces.append((ace[0][0], ace[0][1], ace[1], security.ConvertSidToStringSid(ace[2])))
    return validate_acl(security.ConvertSidToStringSid(sd.GetSecurityDescriptorOwner()),
          bool(sd.GetSecurityDescriptorControl()[0] & 0x1000), aces,
          consumer_sid=consumer_sid, worker_sid=worker_sid, source=source)


def inspect_current_identity(*, consumer_sid, worker_sid, worker=False):
    _require(os.name == 'nt', 'WINDOWS_REQUIRED')
    import win32api
    import win32security as security
    token = security.OpenProcessToken(win32api.GetCurrentProcess(), security.TOKEN_QUERY)
    try:
        sid = security.ConvertSidToStringSid(security.GetTokenInformation(token, security.TokenUser)[0])
        groups = {security.ConvertSidToStringSid(s) for s, _ in
                  security.GetTokenInformation(token, security.TokenGroups)}
        if worker:
            _require(sid == worker_sid and consumer_sid not in groups
                     and SYSTEM_SID not in groups and 'S-1-5-32-544' not in groups,
                     'WORKER_TOKEN_PRINCIPAL_OR_GROUP_CONFLICT')
            _require(not security.GetTokenInformation(token, security.TokenElevation)
                     and bool(security.GetTokenInformation(token, security.TokenRestrictedSids)),
                     'RESTRICTED_NONELEVATED_WORKER_TOKEN_REQUIRED')
            for luid, attributes in security.GetTokenInformation(token, security.TokenPrivileges):
                if attributes & 2:
                    _require(security.LookupPrivilegeName(None, luid) == 'SeChangeNotifyPrivilege',
                             'UNEXPECTED_ENABLED_WORKER_PRIVILEGE')
        else:
            _require(sid == consumer_sid and sid != worker_sid, 'TRUSTED_CONSUMER_IDENTITY_REQUIRED')
        return dict(sid=sid, worker=worker, groups=sorted(groups))
    finally:
        token.Close()


def inspect_protected_store(directory, context):
    _require(type(context) is dict and set(context) >= {'consumer_sid', 'worker_sid'},
             'TRUSTED_WINDOWS_CONTEXT_REQUIRED')
    inspect_current_identity(consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'])
    directory = reject_reparse_chain(directory)
    # Parent DELETE_CHILD / replacement permissions are part of the boundary.
    for item in (directory, *directory.parents):
        inspect_acl(item, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'], source=False)
    for item in directory.iterdir():
        _require(item.is_file() and not item.is_symlink(), 'UNEXPECTED_STORE_ENTRY')
        inspect_acl(item, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'], source=False)
    return 'WINDOWS_STORE_ACL_CHECKED_NOT_DURABILITY_VALIDATED'


def prepare_snapshot(source_manifest, layout, *, repository, destination):
    """Offline provisioner only: exclusive new copy, no ACL changes, no launch.

    layout is an externally approved source-name -> relative-copy-name map.
    A copied tree is only SOURCE_BYTES_VERIFIED until separately protected.
    Partial copies remain on failure and must not be reused or run.
    """
    root, target = Path(repository).resolve(), Path(destination).absolute()
    _require(set(source_manifest) == set(layout) and not target.exists(), 'SNAPSHOT_LAYOUT_CONFLICT')
    destinations = []
    for name, relative in layout.items():
        path = Path(relative)
        _require(not path.is_absolute() and '..' not in path.parts and path.parts,
                 'SNAPSHOT_PATH_ESCAPE')
        destinations.append(str(path).casefold())
    _require(len(destinations) == len(set(destinations)), 'SNAPSHOT_DESTINATION_COLLISION')
    target.mkdir(parents=False, exist_ok=False)
    for name, relative in layout.items():
        original = Path(name) if Path(name).is_absolute() else root / name
        reject_reparse_chain(original)
        _require(hashlib.sha256(original.read_bytes()).hexdigest() == source_manifest[name], 'SNAPSHOT_SOURCE_DRIFT')
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        with original.open('rb') as src, output.open('xb') as dst:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        _require(hashlib.sha256(output.read_bytes()).hexdigest() == source_manifest[name], 'SNAPSHOT_COPY_DRIFT')
    return dict(status='SOURCE_BYTES_VERIFIED', execution_isolated=False)


def inspect_snapshot(root, layout, manifest, context):
    root = reject_reparse_chain(root)
    _require(set(layout) == set(manifest), 'SNAPSHOT_LAYOUT_CONFLICT')
    expected = set()
    for name, relative in layout.items():
        relative = Path(relative)
        _require(not relative.is_absolute() and '..' not in relative.parts, 'SNAPSHOT_PATH_ESCAPE')
        path = root / relative
        reject_reparse_chain(path)
        _require(path.resolve().is_relative_to(root.resolve()), 'SNAPSHOT_PATH_ESCAPE')
        _require(hashlib.sha256(path.read_bytes()).hexdigest() == manifest[name], 'SNAPSHOT_BYTES_CHANGED')
        expected.add(path.resolve())
    actual = set()
    for path in (root, *root.rglob('*')):
        reject_reparse_chain(path)
        inspect_acl(path, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'], source=True)
        if path.is_file():
            actual.add(path.resolve())
    _require(actual == expected, 'UNDECLARED_RUNTIME_FILE')
    # Parent directory rights can replace the entire snapshot.
    for parent in root.parents:
        inspect_acl(parent, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'], source=False)
    return dict(source_bytes='SOURCE_BYTES_VERIFIED', source_execution='NOT_ISOLATED',
                reason='RESTRICTED_PROCESS_CREATION_AND_PYTHON_DLL_LOAD_ENFORCEMENT_NOT_IMPLEMENTED')
