"""ENG release entry. All real RUNs are blocked before science construction."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.non_oracle.stfbs_lite_real_d60_source import production_dispatcher, AdmissionRejected


def main():
    try:
        production_dispatcher()
    except AdmissionRejected:
        print('RUN_ADMISSION_BLOCKED: RUN_HARD_TIME_GUARD_NOT_READY')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
