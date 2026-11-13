import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("FORMAL_RUN",),required=True)
    for name in ("world","announcements","workspace","output","pins"):
        p.add_argument("--"+name,required=True)
    args=p.parse_args()
    from research.non_oracle.sw3_release_runtime import run
    run(args)
if __name__=="__main__":
    main()
