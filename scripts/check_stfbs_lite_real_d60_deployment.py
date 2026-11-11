"""Read-only deployment inspection entry. Never provisions ACLs/accounts/keys.

Not executed by V1.2. The current backend deliberately ends BLOCKED even if
owner/DACL/copy checks pass: restricted-token Job creation and authenticated
bootstrap plus Python/DLL load closure have not been implemented/validated.
"""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.non_oracle.stfbs_lite_real_d60_run_gates import load_production_authority
from research.non_oracle.stfbs_lite_real_d60_windows_boundary import inspect_protected_store
from research.non_oracle.stfbs_lite_real_d60_source import AdmissionRejected


def main():
    try:
        authority = load_production_authority()
        print(inspect_protected_store(authority.consumption_directory, authority.execution_context))
        print('SOURCE_PREFLIGHT_NOT_READY: RESTRICTED_WORKER_AND_DEPENDENCY_CLOSURE_NOT_IMPLEMENTED')
        return 2
    except (AdmissionRejected, OSError, ValueError, ImportError) as exc:
        print('DEPLOYMENT_NOT_READY: ' + str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
