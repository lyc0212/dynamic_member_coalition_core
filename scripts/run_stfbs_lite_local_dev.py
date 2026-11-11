"""LOCAL_DEV parent only. Writing code does not authorize execution."""
import argparse
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.non_oracle.stfbs_lite_local_dev import run_parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization',type=Path,required=True)
    parser.add_argument('--approved-sha256',required=True)
    args=parser.parse_args()
    try:
        result=run_parent(args.authorization,args.approved_sha256,Path(__file__).resolve().parents[1])
        print(result['status'])
        if 'error' in result:
            print(result['error'])
        if 'failure_evidence_persistence' in result:
            print(result['failure_evidence_persistence'])
        return 0 if result['status']=='LOCAL_DEV_EXECUTION_COMPLETE' else 2
    except Exception as exc:
        print('LOCAL_DEV_EXECUTION_REFUSED: '+str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
