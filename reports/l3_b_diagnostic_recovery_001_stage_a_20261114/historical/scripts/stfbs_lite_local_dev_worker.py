"""LOCAL_DEV Job worker. Direct uncontained execution is rejected."""
import argparse
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.non_oracle.stfbs_lite_local_dev import worker_main


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization',type=Path,required=True)
    parser.add_argument('--approved-sha256',required=True)
    parser.add_argument('--handoff',type=Path,required=True)
    args=parser.parse_args()
    return worker_main(args.authorization,args.approved_sha256,args.handoff,Path(__file__).resolve().parents[1])


if __name__ == '__main__':
    raise SystemExit(main())
