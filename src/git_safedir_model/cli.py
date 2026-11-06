"""git-safedir-model: run one scenario (JSON) and print results per mode."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .scenario import load, run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="git-safedir-model", description=__doc__)
    ap.add_argument("scenario", type=Path)
    ap.add_argument("--mode", choices=["pre_fix", "fix_8959555", "fix_0f85c4a"])
    a = ap.parse_args(argv)
    out = run(load(a.scenario))
    if a.mode:
        out = out[a.mode]
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0
