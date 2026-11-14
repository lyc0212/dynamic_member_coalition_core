"""Parent gate entry; unfinished isolation/store gates forbid science launch."""
import argparse
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.non_oracle.stfbs_lite_real_d60_source import check_run_admission, AdmissionRejected
from research.non_oracle.stfbs_lite_real_d60_run_gates import launch_protected_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', type=Path, help='Signed gate request; never a permit issuer')
    args = parser.parse_args()
    try:
        if args.request is None:
            raise AdmissionRejected(check_run_admission()['reason'])
        launch_protected_run(args.request)
    except (AdmissionRejected, OSError, ValueError, KeyError, TypeError) as exc:
        print('RUN_ADMISSION_BLOCKED: ' + str(exc))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
