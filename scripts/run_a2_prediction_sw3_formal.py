"""Separate formal entry. Formal execution is deliberately closed for FI."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.non_oracle.sw3_formal_core import Coordinator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("IMPLEMENTATION_TEST","FORMAL_RUN"), required=True)
    parser.parse_args()
    raise SystemExit("FORMAL_RUN is not authorized. Implementation tests use the shared Coordinator directly.")


if __name__ == "__main__":
    main()
